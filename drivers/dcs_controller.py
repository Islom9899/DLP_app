"""
UDP client for Advanced Illumination DCS Series lighting controller.
ASCII command protocol over UDP socket.

Protocol reference: Advanced Illumination DCS-100E/DCS-103E User Manual
Command format: SET:PARAMETER:CHANNELx,value;
Query format:   GET:PARAMETER:CHANNELx;
"""

import socket
import threading
import logging

logger = logging.getLogger(__name__)


class DCSController:
    """
    UDP client for Advanced Illumination DCS Series controller.
    Thread-safe for use from GUI threads.
    Supports per-channel control of modes, intensity, pulse, trigger settings.
    """

    DEFAULT_PORT = 7777
    RECV_BUFFER = 1024
    ENCODING = 'ascii'
    TIMEOUT = 5.0

    MAX_CURRENT_MA = 400

    # Mode constants
    MODE_OFF = 0
    MODE_CONTINUOUS = 1
    MODE_PULSED = 2
    MODE_GATED = 3

    MODE_NAMES = {0: 'Off', 1: 'Continuous', 2: 'Pulsed', 3: 'Gated'}
    MODE_FROM_NAME = {'Off': 0, 'Continuous': 1, 'Pulsed': 2, 'Gated': 3}

    CHANNELS = ["CHANNEL1", "CHANNEL2", "CHANNEL3"]

    def __init__(self, ip_address: str = "192.168.0.1",
                 port: int = DEFAULT_PORT,
                 channel: str = "CHANNEL1"):
        self.ip_address = ip_address
        self.port = port
        self.channel = channel
        self._socket = None
        self._lock = threading.Lock()
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    def connect(self) -> bool:
        """Create UDP socket and verify DCS controller is reachable."""
        try:
            self.disconnect()
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.settimeout(self.TIMEOUT)
            # Verify controller is reachable by sending a query
            self._socket.sendto(
                f"GET:MODE:{self.channel};".encode(self.ENCODING),
                (self.ip_address, self.port)
            )
            data, _ = self._socket.recvfrom(self.RECV_BUFFER)
            self._connected = True
            logger.info(f"Connected to DCS at {self.ip_address}:{self.port}")
            return True
        except (socket.error, socket.timeout, OSError) as e:
            self._connected = False
            if self._socket:
                try:
                    self._socket.close()
                except socket.error:
                    pass
                self._socket = None
            logger.error(f"DCS connection failed: {e}")
            return False

    def disconnect(self):
        """Close UDP socket."""
        if self._socket:
            try:
                self._socket.close()
            except socket.error:
                pass
            self._socket = None
        self._connected = False

    def _send_command(self, command: str) -> str:
        """
        Send ASCII command via UDP and return response.
        Thread-safe.

        :param command: ASCII command string (e.g. "SET:MODE:CHANNEL1,1;")
        :return: response string from controller
        :raises ConnectionError: if not connected or communication fails
        """
        if not self._connected or self._socket is None:
            raise ConnectionError("Not connected to DCS controller")

        with self._lock:
            try:
                self._socket.sendto(
                    command.encode(self.ENCODING),
                    (self.ip_address, self.port)
                )
                data, _ = self._socket.recvfrom(self.RECV_BUFFER)
                return data.decode(self.ENCODING).strip()
            except socket.timeout:
                raise ConnectionError("DCS controller response timed out")
            except socket.error as e:
                self._connected = False
                raise ConnectionError(f"DCS communication error: {e}")

    # =========================================================================
    # Mode control
    # =========================================================================
    def set_mode(self, mode: int, channel: str = None) -> str:
        """
        Set channel operating mode.

        :param mode: 0=Off, 1=Continuous, 2=Pulsed, 3=Gated
        :param channel: target channel (defaults to self.channel)
        """
        ch = channel or self.channel
        if mode not in self.MODE_NAMES:
            raise ValueError(f"Invalid mode {mode}. Use 0-3")
        return self._send_command(f"SET:MODE:{ch},{mode};")

    def set_mode_by_name(self, mode_name: str, channel: str = None) -> str:
        """Set mode by name: 'Off', 'Continuous', 'Pulsed', or 'Gated'."""
        if mode_name not in self.MODE_FROM_NAME:
            raise ValueError(f"Invalid mode name '{mode_name}'")
        return self.set_mode(self.MODE_FROM_NAME[mode_name], channel)

    def get_mode(self, channel: str = None) -> str:
        """Query current channel mode."""
        ch = channel or self.channel
        return self._send_command(f"GET:MODE:{ch};")

    # =========================================================================
    # Intensity / level control
    # =========================================================================
    def set_level(self, level_ma: int, channel: str = None) -> str:
        """
        Set current level in milliamps.

        :param level_ma: 0-400 mA
        :param channel: target channel (defaults to self.channel)
        """
        ch = channel or self.channel
        level_ma = max(0, min(self.MAX_CURRENT_MA, int(level_ma)))
        return self._send_command(f"SET:LEVEL:{ch},{level_ma};")

    def get_level(self, channel: str = None) -> str:
        """Query current level."""
        ch = channel or self.channel
        return self._send_command(f"GET:LEVEL:{ch};")

    def set_intensity_percent(self, percent: float, channel: str = None) -> str:
        """
        Set intensity as a percentage (0-100%).
        Maps linearly to 0-400 mA.

        :param percent: 0.0 to 100.0
        :param channel: target channel (defaults to self.channel)
        """
        percent = max(0.0, min(100.0, percent))
        level_ma = int(percent * self.MAX_CURRENT_MA / 100.0)
        return self.set_level(level_ma, channel)

    # =========================================================================
    # Pulse width / delay
    # =========================================================================
    def set_pulse_width(self, width_us: int, channel: str = None) -> str:
        """
        Set pulse width in microseconds.

        :param width_us: pulse width in µs
        :param channel: target channel
        """
        ch = channel or self.channel
        width_us = max(0, int(width_us))
        return self._send_command(f"SET:PULSEWIDTH:{ch},{width_us};")

    def get_pulse_width(self, channel: str = None) -> str:
        """Query pulse width."""
        ch = channel or self.channel
        return self._send_command(f"GET:PULSEWIDTH:{ch};")

    def set_pulse_delay(self, delay_us: int, channel: str = None) -> str:
        """
        Set pulse delay in microseconds.

        :param delay_us: pulse delay in µs
        :param channel: target channel
        """
        ch = channel or self.channel
        delay_us = max(0, int(delay_us))
        return self._send_command(f"SET:PULSEDELAY:{ch},{delay_us};")

    def get_pulse_delay(self, channel: str = None) -> str:
        """Query pulse delay."""
        ch = channel or self.channel
        return self._send_command(f"GET:PULSEDELAY:{ch};")

    # =========================================================================
    # Trigger control
    # =========================================================================
    def set_trigger_edge(self, rising: bool = True, channel: str = None) -> str:
        """
        Set trigger edge.

        :param rising: True for rising edge, False for falling edge
        :param channel: target channel
        """
        ch = channel or self.channel
        edge = 0 if rising else 1
        return self._send_command(f"SET:TRIGGEREDGE:{ch},{edge};")

    def get_trigger_edge(self, channel: str = None) -> str:
        """Query trigger edge setting."""
        ch = channel or self.channel
        return self._send_command(f"GET:TRIGGEREDGE:{ch};")

    def set_trigger_input(self, input_num: int, channel: str = None) -> str:
        """
        Set trigger input number.

        :param input_num: trigger input number
        :param channel: target channel
        """
        ch = channel or self.channel
        return self._send_command(f"SET:TRIGGERINPUT:{ch},{int(input_num)};")

    def get_trigger_input(self, channel: str = None) -> str:
        """Query trigger input."""
        ch = channel or self.channel
        return self._send_command(f"GET:TRIGGERINPUT:{ch};")

    # =========================================================================
    # Frequency
    # =========================================================================
    def get_frequency(self, channel: str = None) -> str:
        """Query current frequency."""
        ch = channel or self.channel
        return self._send_command(f"GET:FREQUENCY:{ch};")

    def set_frequency(self, freq_hz: float, channel: str = None) -> str:
        """
        Set frequency in Hz.

        :param freq_hz: frequency in Hz
        :param channel: target channel
        """
        ch = channel or self.channel
        return self._send_command(f"SET:FREQUENCY:{ch},{freq_hz};")

    # =========================================================================
    # Pulse trigger
    # =========================================================================
    def pulse(self, channel: str = None) -> str:
        """Send a single pulse trigger command."""
        ch = channel or self.channel
        return self._send_command(f"SET:PULSE:{ch};")

    # =========================================================================
    # Profile save / load
    # =========================================================================
    def save_profile(self, profile_id: int) -> str:
        """Save current settings to a profile slot."""
        return self._send_command(f"SET:SAVE:{int(profile_id)};")

    def load_profile(self, profile_id: int) -> str:
        """Load settings from a profile slot."""
        return self._send_command(f"SET:LOAD:{int(profile_id)};")

    # =========================================================================
    # Convenience methods
    # =========================================================================
    def turn_on(self, mode: int = MODE_CONTINUOUS, channel: str = None) -> str:
        """Turn on light in specified mode."""
        return self.set_mode(mode, channel)

    def turn_off(self, channel: str = None) -> str:
        """Turn off light."""
        return self.set_mode(self.MODE_OFF, channel)

    def turn_off_all(self):
        """Turn off all channels."""
        for ch in self.CHANNELS:
            try:
                self.set_mode(self.MODE_OFF, ch)
            except Exception:
                pass

    def is_connected(self) -> bool:
        """Check if connection is still alive by sending a query."""
        if not self._connected:
            return False
        try:
            self.get_mode()
            return True
        except (ConnectionError, Exception):
            self._connected = False
            return False

    def __del__(self):
        self.disconnect()
