# SPDX-FileCopyrightText: 2026 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""Tests for runtime platform dependency handling."""

from types import SimpleNamespace

from adafruit_blinka import platform_dependencies


def _detector(chip_id=None, **board_values):
    values = {
        "any_raspberry_pi_5_board": False,
        "any_raspberry_pi": False,
        "any_jetson_board": False,
        "any_beaglebone": False,
    }
    values.update(board_values)
    return SimpleNamespace(
        board=SimpleNamespace(**values), chip=SimpleNamespace(id=chip_id)
    )


def test_raspberry_pi_5_uses_adafruit_lgpio_on_python_313():
    dependencies = platform_dependencies.get_platform_dependencies(
        _detector(any_raspberry_pi_5_board=True, any_raspberry_pi=True),
        python_version=(3, 13),
    )

    assert dependencies == [
        ("lgpio", "adafruit-lgpio>=0.2.2.0"),
        (
            "adafruit_raspberry_pi5_neopixel_write",
            "Adafruit-Blinka-Raspberry-Pi5-Neopixel",
        ),
    ]


def test_raspberry_pi_5_uses_upstream_lgpio_before_python_313():
    dependencies = platform_dependencies.get_platform_dependencies(
        _detector(any_raspberry_pi_5_board=True, any_raspberry_pi=True),
        python_version=(3, 12),
    )

    assert ("lgpio", "lgpio>=0.2.2.0") in dependencies


def test_raspberry_pi_5_neopixel_requires_python_311():
    dependencies = platform_dependencies.get_platform_dependencies(
        _detector(any_raspberry_pi_5_board=True, any_raspberry_pi=True),
        python_version=(3, 10),
    )

    assert all(
        module_name != "adafruit_raspberry_pi5_neopixel_write"
        for module_name, _ in dependencies
    )


def test_earlier_raspberry_pi_does_not_install_lgpio():
    dependencies = platform_dependencies.get_platform_dependencies(
        _detector(any_raspberry_pi=True), python_version=(3, 13)
    )

    assert dependencies == [
        ("RPi.GPIO", "RPi.GPIO"),
        ("_rpi_ws281x", "rpi_ws281x>=4.0.0"),
    ]


def test_import_requirement_uses_detected_python_version():
    detector = _detector(any_raspberry_pi_5_board=True, any_raspberry_pi=True)

    requirement = platform_dependencies.get_platform_requirement_for_import(
        detector, "lgpio", python_version=(3, 12)
    )

    assert requirement == "lgpio>=0.2.2.0"


def test_installer_uses_running_python(monkeypatch):
    detector = _detector(chip_id="AM33XX", any_beaglebone=True)
    commands = []

    monkeypatch.setattr(
        platform_dependencies,
        "get_missing_platform_dependencies",
        lambda *_args, **_kwargs: ["Adafruit_BBIO>=1.2.4"],
    )
    monkeypatch.setattr(platform_dependencies.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(platform_dependencies.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(
        platform_dependencies.subprocess,
        "run",
        lambda command, check: commands.append((command, check)),
    )

    installed = platform_dependencies.install_missing_platform_dependencies(
        detector, input_func=lambda _prompt: "y"
    )

    assert installed is True
    assert commands == [
        (
            [
                platform_dependencies.sys.executable,
                "-m",
                "pip",
                "install",
                "Adafruit_BBIO>=1.2.4",
            ],
            True,
        )
    ]


def test_installer_skips_prompt_without_terminal(monkeypatch):
    detector = _detector(chip_id="AM33XX", any_beaglebone=True)
    prompted = []

    monkeypatch.setattr(
        platform_dependencies,
        "get_missing_platform_dependencies",
        lambda *_args, **_kwargs: ["Adafruit_BBIO>=1.2.4"],
    )
    monkeypatch.setattr(platform_dependencies.sys.stdin, "isatty", lambda: False)

    installed = platform_dependencies.install_missing_platform_dependencies(
        detector, input_func=prompted.append
    )

    assert installed is False
    assert not prompted
