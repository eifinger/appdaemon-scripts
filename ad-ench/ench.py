"""EnCh.
   Entity Checker

  @benleb / https://github.com/benleb/ad-ench
"""

__version__ = "0.9.0"

from datetime import datetime, timedelta
from fnmatch import fnmatch
from pprint import pformat
from sys import version_info
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import hassapi as hass


APP_NAME = "EnCh"
APP_ICON = "👩‍⚕️"

BATTERY_MIN_LEVEL = 20
INTERVAL_BATTERY_MIN = 180
INTERVAL_BATTERY = INTERVAL_BATTERY_MIN / 60

INTERVAL_UNAVAILABLE_MIN = 60
INTERVAL_UNAVAILABLE = INTERVAL_UNAVAILABLE_MIN / 60
MAX_UNAVAILABLE_MIN = 0

INTERVAL_STALE_MIN = 15
MAX_STALE_MIN = 60

INITIAL_DELAY = 60

RANDOMIZE_SEC: int = 15
SECONDS_PER_MIN: int = 60

EXCLUDE = ["binary_sensor.updater", "persistent_notification.config_entry_discovery"]
BAD_STATES = ["unavailable", "unknown"]
LEVEL_ATTRIBUTES = ["battery_level", "Battery Level"]
CHECKS = ["battery", "stale", "unavailable"]

ICONS: Dict[str, str] = dict(battery="🔋", unavailable="⁉️ ", unknown="❓", stale="⏰")


# version checks
py3_or_higher = version_info.major >= 3
py37_or_higher = py3_or_higher and version_info.minor >= 7
py38_or_higher = py3_or_higher and version_info.minor >= 8


def hl(text: Union[int, float, str]) -> str:
    return f"\033[1m{text}\033[0m"


def hl_entity(entity: str) -> str:
    if len(splitted := entity.split(".")) > 1:
        return f"{splitted[0]}.{hl(splitted[1])}"
    else:
        return f"{hl(entity)}"


class EnCh(hass.Hass):  # type: ignore
    """EnCh."""

    def lg(self, msg: str, *args: Any, icon: Optional[str] = None, repeat: int = 1, **kwargs: Any) -> None:
        kwargs.setdefault("ascii_encode", False)
        message = f"{f'{icon} ' if icon else ' '}{msg}"
        _ = [self.log(message, *args, **kwargs) for _ in range(repeat)]

    async def initialize(self) -> None:
        """Register API endpoint."""
        self.icon = APP_ICON

        # python version check
        if not py38_or_higher:
            icon_alert = "⚠️"
            self.lg("", icon=icon_alert)
            self.lg("")
            self.lg(f"please update to {hl('Python >= 3.8')}! 🤪", icon=icon_alert)
            self.lg("")
            self.lg("", icon=icon_alert)
        if not py37_or_higher:
            raise ValueError

        self.cfg: Dict[str, Any] = dict()
        self.cfg["show_friendly_name"] = bool(self.args.get("show_friendly_name", True))
        self.cfg["init_delay_secs"] = int(self.args.get("initial_delay_secs", INITIAL_DELAY))

        # home assistant sensor
        hass_sensor: str
        if hass_sensor := self.args.get("hass_sensor", "sensor.ench_entities"):
            self.cfg["hass_sensor"] = hass_sensor if hass_sensor.startswith("sensor.") else f"sensor.{hass_sensor}"
            self.sensor_state: int = 0
            self.sensor_attrs: Dict[str, Any] = {check: [] for check in CHECKS}
            self.sensor_attrs.update({"unit_of_measurement": "Entities", "should_poll": False})

        # global notification
        if "notify" in self.args:
            self.cfg["notify"] = self.args.get("notify")

        # initial wait to give all devices a chance to become available
        init_delay = await self.datetime() + timedelta(seconds=self.cfg["init_delay_secs"])

        # battery check
        if "battery" in self.args:

            config: Dict[str, Union[str, int]] = self.args.get("battery")

            # store configuration
            self.cfg["battery"] = dict(
                interval_min=int(config.get("interval_min", INTERVAL_BATTERY_MIN)),
                min_level=int(config.get("min_level", BATTERY_MIN_LEVEL)),
            )

            # no, per check or global notification
            self.choose_notify_recipient("battery", config)

            # schedule check
            await self.run_every(
                self.check_battery,
                init_delay,
                self.cfg["battery"]["interval_min"] * 60,
                random_start=-RANDOMIZE_SEC,
                random_end=RANDOMIZE_SEC,
            )

        # unavailable check
        if "unavailable" in self.args:

            config = self.args.get("unavailable")

            # store configuration
            self.cfg["unavailable"] = dict(
                interval_min=int(config.get("interval_min", INTERVAL_UNAVAILABLE_MIN)),
                max_unavailable_min=int(config.get("max_unavailable_min", MAX_UNAVAILABLE_MIN)),
            )

            # no, per check or global notification
            self.choose_notify_recipient("unavailable", config)

            # schedule check
            self.run_every(
                self.check_unavailable,
                await self.datetime() + timedelta(seconds=self.cfg["init_delay_secs"]),
                self.cfg["unavailable"]["interval_min"] * 60,
                random_start=-RANDOMIZE_SEC,
                random_end=RANDOMIZE_SEC,
            )

        # stale entities check
        if "stale" in self.args:

            config = self.args.get("stale", {})
            interval_min = config.get("interval_min", INTERVAL_STALE_MIN)
            max_stale_min = config.get("max_stale_min", MAX_STALE_MIN)

            # store configuration
            self.cfg["stale"] = dict(
                interval_min=int(min([interval_min, max_stale_min])),
                max_stale_min=int(max_stale_min),
            )

            self.cfg["stale"]["entities"] = config.get("entities", [])

            # no, per check or global notification
            self.choose_notify_recipient("stale", config)

            # schedule check
            self.run_every(
                self.check_stale,
                await self.datetime() + timedelta(seconds=self.cfg["init_delay_secs"]),
                self.cfg["stale"]["interval_min"] * 60,
                random_start=-RANDOMIZE_SEC,
                random_end=RANDOMIZE_SEC,
            )

        # merge excluded entities
        exclude = set(EXCLUDE)
        exclude.update([e.lower() for e in self.args.get("exclude", set())])
        self.cfg["exclude"] = sorted(list(exclude))

        # set units
        self.cfg.setdefault(
            "_units",
            dict(interval_min="min", max_stale_min="min", min_level="%"),
        )

        self.show_info(self.args)

    async def check_battery(self, _: Any) -> None:
        """Handle scheduled checks."""
        check_config = self.cfg["battery"]
        results: List[Tuple[str, int]] = []

        self.lg("Checking entities for low battery levels...", icon=APP_ICON, level="DEBUG")

        states = await self.get_state()

        entities = filter(
            lambda entity: not any(fnmatch(entity, pattern) for pattern in self.cfg["exclude"]),
            states,
        )

        for entity in sorted(entities):
            battery_level = None

            try:
                # check entities which may be battery level sensors
                if "battery_level" in entity or "battery" in entity:
                    # battery_level = int(await self.get_state(entity))
                    battery_level = int(states[entity]["state"])

                # check entity attributes for battery levels
                if not battery_level:
                    for attr in LEVEL_ATTRIBUTES:
                        # battery_level = int(await self.get_state(entity, attribute=attr))
                        battery_level = int(states[entity]["attributes"].get(attr))
                        break
            except (TypeError, ValueError):
                pass

            if battery_level and battery_level <= check_config["min_level"]:
                # results.append(entity)
                results.append((entity, battery_level))
                last_updated = (await self.last_update(entity)).time().isoformat(timespec="seconds")
                self.lg(
                    f"{await self._name(entity)} has low "
                    # f"{hl(f'battery → {hl(int(battery_level))}')}%",
                    f"{hl(f'battery → {hl(int(battery_level))}')}% | " f"last update: {last_updated}",
                    # f"last update: {self.adu.last_update(entity)}",
                    icon=ICONS["battery"],
                )

        # send notification
        notify = self.cfg.get("notify") or check_config.get("notify")
        if notify and results:
            await self.call_service(
                str(notify).replace(".", "/"),
                message=f"{ICONS['battery']} Battery low ({len(results)}): "
                f"{', '.join([f'{str(await self._name(entity[0], notification=True))} {entity[1]}%' for entity in results])}",  # noqa
            )

        # update hass sensor
        if "hass_sensor" in self.cfg and self.cfg["hass_sensor"]:
            await self.update_sensor("battery", [entity[0] for entity in results])

        self._print_result("battery", [entity[0] for entity in results], "low battery levels")

    async def check_unavailable(self, _: Any) -> None:
        """Handle scheduled checks."""
        check_config = self.cfg["unavailable"]
        results: List[str] = []

        self.lg("Checking entities for unavailable/unknown state...", icon=APP_ICON, level="DEBUG")

        entities = filter(
            lambda entity: not any(fnmatch(entity, pattern) for pattern in self.cfg["exclude"]),
            await self.get_state(),
        )

        for entity in sorted(entities):
            state = await self.get_state(entity_id=entity)

            if state in BAD_STATES and entity not in results:

                last_update = await self.last_update(entity)
                now: datetime = await self.datetime(aware=True)
                unavailable_time: timedelta = now - last_update
                max_unavailable_min = timedelta(minutes=self.cfg["unavailable"]["max_unavailable_min"])

                if unavailable_time >= max_unavailable_min:
                    results.append(entity)
                    last_updated = (await self.last_update(entity)).time().isoformat(timespec="seconds")
                    self.lg(
                        f"{await self._name(entity)} is "
                        f"{hl(state)} since {hl(int(unavailable_time.seconds / 60))}min | "
                        f"last update: {last_updated}",
                        icon=ICONS[state],
                    )
                    # self.lg(
                    #     f"{await self._name(entity)} is {hl(state)} | " f"last update: {last_updated}",
                    #     icon=ICONS[state],
                    # )

        # send notification
        notify = self.cfg.get("notify") or check_config.get("notify")
        if notify and results:
            self.call_service(
                str(notify).replace(".", "/"),
                message=f"{APP_ICON} Unavailable entities ({len(results)}): "
                f"{', '.join([str(await self._name(entity, notification=True)) for entity in results])}",
            )

        # update hass sensor
        if "hass_sensor" in self.cfg and self.cfg["hass_sensor"]:
            await self.update_sensor("unavailable", results)

        self._print_result("unavailable", results, "unavailable/unknown state")

    async def check_stale(self, _: Any) -> None:
        check_config = self.cfg["stale"]
        """Handle scheduled checks."""
        results: List[str] = []

        self.lg("Checking for stale entities...", icon=APP_ICON, level="DEBUG")

        if self.cfg["stale"]["entities"]:
            all_entities = self.cfg["stale"]["entities"]
        else:
            all_entities = await self.get_state()

        entities = filter(
            lambda entity: not any(fnmatch(entity, pattern) for pattern in self.cfg["exclude"]),
            all_entities,
        )

        for entity in sorted(entities):

            attr_last_updated = await self.get_state(entity_id=entity, attribute="last_updated")

            if not attr_last_updated:
                self.lg(f"{await self._name(entity)} has no 'last_updated' attribute ¯\\_(ツ)_/¯", icon=ICONS["stale"])
                continue

            last_update = self.convert_utc(attr_last_updated)
            last_updated = (await self.last_update(entity)).time().isoformat(timespec="seconds")
            now: datetime = await self.datetime(aware=True)

            stale_time: timedelta = now - last_update
            max_stale_min = timedelta(minutes=self.cfg["stale"]["max_stale_min"])

            if stale_time and stale_time >= max_stale_min:
                results.append(entity)
                self.lg(
                    f"{await self._name(entity)} is "
                    f"{hl(f'stale since {hl(int(stale_time.seconds / 60))}')}min | "
                    f"last update: {last_updated}",
                    icon=ICONS["stale"],
                )

        # send notification
        notify = self.cfg.get("notify") or check_config.get("notify")
        if notify and results:
            self.call_service(
                str(notify).replace(".", "/"),
                message=f"{APP_ICON} Stalled entities ({len(results)}): "
                f"{', '.join([str(await self._name(entity, notification=True)) for entity in results])}",
            )

        # update hass sensor
        if "hass_sensor" in self.cfg and self.cfg["hass_sensor"]:
            await self.update_sensor("stale", results)

        self._print_result("stale", results, "stalled updates")

    def choose_notify_recipient(self, check: str, config: Dict[str, Any]) -> None:
        if "notify" in config and "notify" not in self.cfg:
            self.cfg[check]["notify"] = config["notify"]

    async def last_update(self, entity_id: str) -> Any:
        return self.convert_utc(await self.get_state(entity_id=entity_id, attribute="last_updated"))

    async def _name(self, entity: str, friendly_name: bool = False, notification: bool = False) -> Optional[str]:

        name: Optional[str] = None
        if self.cfg["show_friendly_name"]:
            name = await self.friendly_name(entity)
        else:
            name = entity

        if notification is False and name:
            name = hl_entity(name)

        return name

    def _print_result(self, check: str, entities: List[str], reason: str) -> None:
        if entities:
            self.lg(f"{hl(f'{len(entities)} entities')} with {hl(reason)}!", icon=APP_ICON, level="DEBUG")
        else:
            self.lg(f"{hl(f'no entities')} with {hl(reason)}!", icon=APP_ICON)

    async def update_sensor(self, check_name: str, entities: List[str]) -> None:

        if check_name not in CHECKS:
            self.lg(
                f"Unknown check: {hl(f'no entities')} - {self.cfg['hass_sensor']} not updated!",
                icon=APP_ICON,
                level="ERROR",
            )

        if len(self.sensor_attrs[check_name]) != len(entities):

            self.sensor_attrs[check_name] = entities
            self.sensor_state = sum([len(self.sensor_attrs[check]) for check in CHECKS])
            self.set_state(self.cfg["hass_sensor"], state=self.sensor_state, attributes=self.sensor_attrs)

            self.lg(
                f"{hl_entity(self.cfg['hass_sensor'])} -> {hl(self.sensor_state)} "
                f"| {', '.join([f'{hl(k) if k == check_name else k}: {hl(len(v))}' for k, v in self.sensor_attrs.items() if type(v) == list])}",
                icon=APP_ICON,
                level="INFO",
            )

    def show_info(self, config: Optional[Dict[str, Any]] = None) -> None:
        # check if a room is given
        if config:
            self.config = config

        if not self.config:
            self.lg("no configuration available", icon="‼️", level="ERROR")
            return

        room = ""
        if "room" in self.config:
            room = f" - {hl(self.config['room'].capitalize())}"

        self.lg("")
        self.lg(f"{hl(APP_NAME)} v{hl(__version__)}{room}", icon=self.icon)
        self.lg("")

        listeners = self.config.pop("listeners", None)

        for key, value in self.config.items():

            # hide "internal keys" when displaying config
            if key in ["module", "class"] or key.startswith("_"):
                continue

            if isinstance(value, list):
                self.print_collection(key, value, 2)
            elif isinstance(value, dict):
                self.print_collection(key, value, 2)
            else:
                self._print_cfg_setting(key, value, 2)

        if listeners:
            self.lg("  event listeners:")
            for listener in sorted(listeners):
                self.lg(f"    - {hl(listener)}")

        self.lg("")

    def print_collection(self, key: str, collection: Iterable[Any], indentation: int = 2) -> None:

        self.log(f"{indentation * ' '}{key}:")
        indentation = indentation + 2

        for item in collection:
            indent = indentation * " "

            if isinstance(item, dict):
                if "name" in item:
                    self.print_collection(item.pop("name", ""), item, indentation)
                else:
                    self.log(f"{indent}{hl(pformat(item, compact=True))}")

            elif isinstance(collection, dict):
                self._print_cfg_setting(item, collection[item], indentation)

            else:
                self.log(f"{indent}- {hl(item)}")

    def _print_cfg_setting(self, key: str, value: Union[int, str], indentation: int) -> None:
        unit = prefix = ""
        indent = indentation * " "

        # legacy way
        if key == "delay" and isinstance(value, int):
            unit = "min"
            min_value = f"{int(value / 60)}:{int(value % 60):02d}"
            self.log(f"{indent}{key}: {prefix}{hl(min_value)}{unit} ~≈ " f"{hl(value)}sec")

        else:
            if "_units" in self.config and key in self.config["_units"]:
                unit = self.config["_units"][key]
            if "_prefixes" in self.config and key in self.config["_prefixes"]:
                prefix = self.config["_prefixes"][key]

            self.log(f"{indent}{key}: {prefix}{hl(value)}{unit}")
