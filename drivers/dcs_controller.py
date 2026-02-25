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
    """

    DEFAULT_PORT = 7777
    RECV_BUFFER = 1024
    ENCODING = 'ascii'
    TIMEOUT = 5.0

    # Mode constants
    MODE_OFF = 0
    MODE_CONTINUOUS = 1
    MODE_STROBE = 2

    MODE_NAMES = {0: 'Off', 1: 'Continuous', 2: 'Strobe'}
    MODE_FROM_NAME = {'Off': 0, 'Continuous': 1, 'Strobe': 2}

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
    def set_mode(self, mode: int) -> str:
        """
        Set channel operating mode.

        :param mode: 0=Off, 1=Continuous, 2=Strobe
        """
        if mode not in self.MODE_NAMES:
            raise ValueError(f"Invalid mode {mode}. Use 0 (Off), 1 (Continuous), or 2 (Strobe)")
        return self._send_command(f"SET:MODE:{self.channel},{mode};")

    def set_mode_by_name(self, mode_name: str) -> str:
        """Set mode by name: 'Off', 'Continuous', or 'Strobe'."""
        if mode_name not in self.MODE_FROM_NAME:
            raise ValueError(f"Invalid mode name '{mode_name}'. Use 'Off', 'Continuous', or 'Strobe'")
        return self.set_mode(self.MODE_FROM_NAME[mode_name])

    def get_mode(self) -> str:
        """Query current channel mode."""
        return self._send_command(f"GET:MODE:{self.channel};")

    # =========================================================================
    # Intensity control
    # =========================================================================
    def set_level(self, level_ma: int) -> str:
        """
        Set current level in milliamps.

        :param level_ma: 0-400 mA
        """
        level_ma = max(0, min(400, int(level_ma)))
        return self._send_command(f"SET:LEVEL:{self.channel},{level_ma};")

    def get_level(self) -> str:
        """Query current level."""
        return self._send_command(f"GET:LEVEL:{self.channel};")

    def set_intensity_percent(self, percent: float) -> str:
        """
        Set intensity as a percentage (0-100%).
        Maps linearly to 0-400 mA.

        :param percent: 0.0 to 100.0
        """
        percent = max(0.0, min(100.0, percent))
        level_ma = int(percent * 4)
        return self.set_level(level_ma)

    # =========================================================================
    # Convenience methods
    # =========================================================================
    def turn_on(self, mode: int = MODE_CONTINUOUS) -> str:
        """Turn on light in specified mode."""
        return self.set_mode(mode)

    def turn_off(self) -> str:
        """Turn off light."""
        return self.set_mode(self.MODE_OFF)

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
