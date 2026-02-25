"""
Internationalization (i18n) module for DLP + DCS Controller.
Supports English and Korean with runtime language switching.
"""

# Available languages
LANGUAGES = {
    "English": "en",
    "한국어": "ko",
}

# Default language
_current_lang = "en"

# Callbacks registered by GUI widgets for language change notifications
_listeners = []


def get_lang() -> str:
    """Return current language code."""
    return _current_lang


def set_lang(lang_code: str):
    """Set language and notify all listeners."""
    global _current_lang
    if lang_code not in ("en", "ko"):
        lang_code = "en"
    _current_lang = lang_code
    for callback in _listeners:
        try:
            callback()
        except Exception:
            pass


def add_listener(callback):
    """Register a callback to be called when language changes."""
    if callback not in _listeners:
        _listeners.append(callback)


def remove_listener(callback):
    """Remove a language change listener."""
    if callback in _listeners:
        _listeners.remove(callback)


def t(key: str) -> str:
    """Translate a key to the current language."""
    lang_strings = _STRINGS.get(_current_lang, _STRINGS["en"])
    return lang_strings.get(key, _STRINGS["en"].get(key, key))


# =========================================================================
# Translation strings
# =========================================================================
_STRINGS = {
    "en": {
        # App
        "app_title": "DLP + DCS Controller",
        "app_started": "Application started. Connect your devices.",
        "language": "Language",

        # Connection panel
        "device_connections": "Device Connections",
        "dlp_usb": "DLP6500 (USB):",
        "dcs_ethernet": "DCS Controller (Ethernet):",
        "disconnected": "Disconnected",
        "connected": "Connected",
        "error": "Error",
        "connect": "Connect",
        "disconnect": "Disconnect",
        "connecting": "Connecting...",
        "ip": "IP:",
        "port": "Port:",

        # Connection messages
        "dlp_connecting": "Connecting to DLP6500...",
        "dlp_connected": "DLP6500 connected successfully",
        "dlp_error": "DLP6500 error: {0}",
        "dlp_disconnected": "DLP6500 disconnected",
        "dcs_connecting": "Connecting to DCS Controller ({0}:{1})...",
        "dcs_connected": "DCS Controller connected successfully",
        "dcs_error": "DCS Controller error: {0}",
        "dcs_disconnected": "DCS Controller disconnected",
        "dcs_connect_failed": "Failed to connect to DCS ({0}:{1})",
        "dmd_type_firmware": "DMD type: {0}, Firmware: {1}",
        "err_no_ip": "Error: IP address not entered",
        "err_port_number": "Error: Port must be a number",

        # DLP panel
        "dlp_pattern_control": "DLP6500 Pattern Control",
        "dlp_available_images": "Available Images",
        "dlp_select_images": "Select Images",
        "dlp_add_all": "Add All >>",
        "dlp_add_to_seq": "Add >",
        "dlp_remove_from_seq": "< Remove",
        "dlp_clear_seq": "Clear All",
        "dlp_sequence_order": "Sequence Order",
        "dlp_move_up": "Move Up",
        "dlp_move_down": "Move Down",
        "dlp_images_added": "{0} image(s) added",
        "dlp_no_selection": "No items selected",
        "dlp_seq_count": "Sequence: {0} pattern(s)",
        "dlp_seq_empty": "Error: Sequence is empty",
        "pattern_mode": "Pattern Mode:",
        "pattern_file": "Pattern File:",
        "select": "Select...",
        "not_selected": "Not selected",
        "exposure_time": "Exposure Time (µs):",
        "min_exposure": "(min: 105 µs)",
        "dark_time": "Dark Time (µs):",
        "wait_trigger": "Wait for Trigger",
        "upload_patterns": "Upload Patterns",
        "uploading": "Uploading...",
        "start": "Start",
        "stop": "Stop",
        "select_pattern_title": "Select pattern file",
        "numpy_files": "NumPy files",
        "tiff_images": "TIFF images",
        "png_images": "PNG images",
        "bmp_images": "BMP images",
        "all_files": "All files",
        "loaded_patterns": "Loaded: {0} patterns, {1}x{2} px",
        "pattern_loaded_log": "Pattern loaded: {0} pcs, size {1}x{2}",
        "unknown_format": "Unknown file format: {0}",
        "pattern_load_error": "Pattern load error: {0}",
        "warn_min_exposure": "Warning: Exposure time must be at least 105 µs",
        "err_exposure_integer": "Error: Exposure time must be an integer",
        "err_select_pattern": "Error: Select a pattern file first",
        "err_dlp_not_connected": "Error: DLP6500 not connected",
        "pattern_uploading": "Uploading pattern... (exp={0}µs, dark={1}µs)",
        "pattern_uploaded": "Pattern uploaded successfully",
        "pattern_uploaded_dmd": "Pattern uploaded to DMD",
        "pattern_upload_error": "Pattern upload error: {0}",
        "dlp_sequence_started": "DLP pattern sequence started",
        "dlp_start_error": "DLP start error: {0}",
        "dlp_sequence_stopped": "DLP pattern sequence stopped",
        "dlp_stop_error": "DLP stop error: {0}",

        # DCS panel
        "dcs_panel_title": "DCS-100E/103E Control",
        "dcs_light_control": "DCS Light Control",
        "dcs_devices": "Devices:",
        "dcs_success": "Success",
        "dcs_profile": "Profile:",
        "dcs_save": "Save",
        "dcs_load": "Load",
        "dcs_channel_control": "Channel Control",
        "dcs_channel_n": "Channel {0}",
        "channel": "Channel:",
        "mode": "Mode:",
        "dcs_pulse_width": "Pulse Width:",
        "dcs_pulse_delay": "Pulse Delay:",
        "dcs_rising": "Rising",
        "dcs_falling": "Falling",
        "dcs_trigger_input": "Trigger Input:",
        "dcs_pulse": "Pulse",
        "dcs_mode_set": "Ch{0} mode: {1}",
        "dcs_pulse_sent": "Pulse sent to Ch{0}",
        "dcs_err_pulse_values": "Error: Pulse values must be numbers",
        "dcs_profile_saved": "Profile {0} saved",
        "dcs_profile_loaded": "Profile {0} loaded",
        "intensity": "Intensity:",
        "exact_value": "Exact value (%):",
        "set_value": "Set",
        "apply_settings": "Apply Settings",
        "turn_on": "Turn On (100%)",
        "turn_off": "Turn Off",
        "err_dcs_not_connected": "Error: DCS Controller not connected",
        "dcs_channel_changed": "DCS channel changed: {0}",
        "dcs_intensity": "DCS intensity: {0:.0f}%",
        "err_intensity_number": "Error: Intensity must be a number",
        "applied_settings": "Applied: {0}, {1}%",
        "dcs_settings_applied": "DCS settings applied: {0}, {1}%",
        "dcs_error_generic": "DCS error: {0}",
        "turned_on": "On: Continuous, 100%",
        "dcs_light_on": "DCS light on: Continuous, 100%",
        "turned_off": "Off",
        "dcs_light_off": "DCS light off",

        # Project panel
        "project_control": "Project Control",
        "project_desc": "When 'Start' is pressed: 1) DCS light turns on  2) DLP projection starts",
        "start_project": "START PROJECT",
        "stop_project": "STOP",
        "ready": "Ready",
        "err_no_device": "Error: No device connected",
        "project_dcs_on": "Project: Turning on DCS light...",
        "dcs_turning_on": "Turning on DCS light...",
        "dcs_light_activated": "DCS light on ({0})",
        "project_dlp_start": "Project: Starting DLP projection...",
        "dlp_starting": "Starting DLP projection...",
        "dlp_projection_started": "DLP projection started",
        "project_running": "Project running",
        "project_started": "Project started successfully",
        "project_error": "Project error: {0}",
        "stopping": "Stopping...",
        "project_stopping": "Stopping project...",
        "dlp_projection_stopped": "DLP projection stopped",
        "dcs_light_turned_off": "DCS light turned off",
        "stopped": "Stopped",
        "project_stopped": "Project stopped",
        "stop_error": "Stop error: {0}",

        # Status bar
        "log": "Log",
        "clear": "Clear",
    },

    "ko": {
        # App
        "app_title": "DLP + DCS 컨트롤러",
        "app_started": "애플리케이션이 시작되었습니다. 장치를 연결하세요.",
        "language": "언어",

        # Connection panel
        "device_connections": "장치 연결",
        "dlp_usb": "DLP6500 (USB):",
        "dcs_ethernet": "DCS 컨트롤러 (이더넷):",
        "disconnected": "연결 안됨",
        "connected": "연결됨",
        "error": "오류",
        "connect": "연결",
        "disconnect": "해제",
        "connecting": "연결 중...",
        "ip": "IP:",
        "port": "포트:",

        # Connection messages
        "dlp_connecting": "DLP6500에 연결 중...",
        "dlp_connected": "DLP6500 연결 성공",
        "dlp_error": "DLP6500 오류: {0}",
        "dlp_disconnected": "DLP6500 연결 해제됨",
        "dcs_connecting": "DCS 컨트롤러에 연결 중 ({0}:{1})...",
        "dcs_connected": "DCS 컨트롤러 연결 성공",
        "dcs_error": "DCS 컨트롤러 오류: {0}",
        "dcs_disconnected": "DCS 컨트롤러 연결 해제됨",
        "dcs_connect_failed": "DCS에 연결할 수 없습니다 ({0}:{1})",
        "dmd_type_firmware": "DMD 유형: {0}, 펌웨어: {1}",
        "err_no_ip": "오류: IP 주소를 입력하지 않았습니다",
        "err_port_number": "오류: 포트는 숫자여야 합니다",

        # DLP panel
        "dlp_pattern_control": "DLP6500 패턴 제어",
        "dlp_available_images": "사용 가능한 이미지",
        "dlp_select_images": "이미지 선택",
        "dlp_add_all": "전체 추가 >>",
        "dlp_add_to_seq": "추가 >",
        "dlp_remove_from_seq": "< 제거",
        "dlp_clear_seq": "전체 삭제",
        "dlp_sequence_order": "시퀀스 순서",
        "dlp_move_up": "위로",
        "dlp_move_down": "아래로",
        "dlp_images_added": "{0}개 이미지 추가됨",
        "dlp_no_selection": "선택된 항목이 없습니다",
        "dlp_seq_count": "시퀀스: {0}개 패턴",
        "dlp_seq_empty": "오류: 시퀀스가 비어 있습니다",
        "pattern_mode": "패턴 모드:",
        "pattern_file": "패턴 파일:",
        "select": "선택...",
        "not_selected": "선택 안됨",
        "exposure_time": "노출 시간 (µs):",
        "min_exposure": "(최소: 105 µs)",
        "dark_time": "다크 타임 (µs):",
        "wait_trigger": "트리거 대기",
        "upload_patterns": "패턴 업로드",
        "uploading": "업로드 중...",
        "start": "시작",
        "stop": "정지",
        "select_pattern_title": "패턴 파일 선택",
        "numpy_files": "NumPy 파일",
        "tiff_images": "TIFF 이미지",
        "png_images": "PNG 이미지",
        "bmp_images": "BMP 이미지",
        "all_files": "모든 파일",
        "loaded_patterns": "로드됨: {0}개 패턴, {1}x{2} px",
        "pattern_loaded_log": "패턴 로드됨: {0}개, 크기 {1}x{2}",
        "unknown_format": "알 수 없는 파일 형식: {0}",
        "pattern_load_error": "패턴 로드 오류: {0}",
        "warn_min_exposure": "경고: 노출 시간은 최소 105 µs 이상이어야 합니다",
        "err_exposure_integer": "오류: 노출 시간은 정수여야 합니다",
        "err_select_pattern": "오류: 먼저 패턴 파일을 선택하세요",
        "err_dlp_not_connected": "오류: DLP6500이 연결되지 않았습니다",
        "pattern_uploading": "패턴 업로드 중... (exp={0}µs, dark={1}µs)",
        "pattern_uploaded": "패턴 업로드 성공",
        "pattern_uploaded_dmd": "패턴이 DMD에 업로드됨",
        "pattern_upload_error": "패턴 업로드 오류: {0}",
        "dlp_sequence_started": "DLP 패턴 시퀀스 시작됨",
        "dlp_start_error": "DLP 시작 오류: {0}",
        "dlp_sequence_stopped": "DLP 패턴 시퀀스 정지됨",
        "dlp_stop_error": "DLP 정지 오류: {0}",

        # DCS panel
        "dcs_panel_title": "DCS-100E/103E 제어",
        "dcs_light_control": "DCS 조명 제어",
        "dcs_devices": "장치:",
        "dcs_success": "성공",
        "dcs_profile": "프로필:",
        "dcs_save": "저장",
        "dcs_load": "불러오기",
        "dcs_channel_control": "채널 제어",
        "dcs_channel_n": "채널 {0}",
        "channel": "채널:",
        "mode": "모드:",
        "dcs_pulse_width": "펄스 폭:",
        "dcs_pulse_delay": "펄스 지연:",
        "dcs_rising": "상승",
        "dcs_falling": "하강",
        "dcs_trigger_input": "트리거 입력:",
        "dcs_pulse": "펄스",
        "dcs_mode_set": "Ch{0} 모드: {1}",
        "dcs_pulse_sent": "Ch{0}에 펄스 전송",
        "dcs_err_pulse_values": "오류: 펄스 값은 숫자여야 합니다",
        "dcs_profile_saved": "프로필 {0} 저장됨",
        "dcs_profile_loaded": "프로필 {0} 불러옴",
        "intensity": "강도:",
        "exact_value": "정확한 값 (%):",
        "set_value": "설정",
        "apply_settings": "설정 적용",
        "turn_on": "켜기 (100%)",
        "turn_off": "끄기",
        "err_dcs_not_connected": "오류: DCS 컨트롤러가 연결되지 않았습니다",
        "dcs_channel_changed": "DCS 채널 변경: {0}",
        "dcs_intensity": "DCS 강도: {0:.0f}%",
        "err_intensity_number": "오류: 강도는 숫자여야 합니다",
        "applied_settings": "적용됨: {0}, {1}%",
        "dcs_settings_applied": "DCS 설정 적용됨: {0}, {1}%",
        "dcs_error_generic": "DCS 오류: {0}",
        "turned_on": "켜짐: Continuous, 100%",
        "dcs_light_on": "DCS 조명 켜짐: Continuous, 100%",
        "turned_off": "꺼짐",
        "dcs_light_off": "DCS 조명 꺼짐",

        # Project panel
        "project_control": "프로젝트 제어",
        "project_desc": "'시작' 버튼을 누르면: 1) DCS 조명 켜짐  2) DLP 프로젝션 시작",
        "start_project": "프로젝트 시작",
        "stop_project": "정지",
        "ready": "준비됨",
        "err_no_device": "오류: 연결된 장치가 없습니다",
        "project_dcs_on": "프로젝트: DCS 조명 켜는 중...",
        "dcs_turning_on": "DCS 조명 켜는 중...",
        "dcs_light_activated": "DCS 조명 켜짐 ({0})",
        "project_dlp_start": "프로젝트: DLP 프로젝션 시작 중...",
        "dlp_starting": "DLP 프로젝션 시작 중...",
        "dlp_projection_started": "DLP 프로젝션 시작됨",
        "project_running": "프로젝트 실행 중",
        "project_started": "프로젝트가 성공적으로 시작되었습니다",
        "project_error": "프로젝트 오류: {0}",
        "stopping": "정지 중...",
        "project_stopping": "프로젝트 정지 중...",
        "dlp_projection_stopped": "DLP 프로젝션 정지됨",
        "dcs_light_turned_off": "DCS 조명 꺼짐",
        "stopped": "정지됨",
        "project_stopped": "프로젝트 정지됨",
        "stop_error": "정지 오류: {0}",

        # Status bar
        "log": "로그",
        "clear": "지우기",
    },
}
