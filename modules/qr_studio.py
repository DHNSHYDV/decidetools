import base64
import io
import qrcode
import qrcode.image.svg
from PIL import ImageColor


class QRStudioError(Exception):
    pass


ERROR_CORRECTION_MAP = {
    "L": qrcode.constants.ERROR_CORRECT_L,
    "M": qrcode.constants.ERROR_CORRECT_M,
    "Q": qrcode.constants.ERROR_CORRECT_Q,
    "H": qrcode.constants.ERROR_CORRECT_H,
}


def build_wifi_payload(ssid: str, password: str = "", auth_type: str = "WPA", hidden: bool = False) -> str:
    """
    Format standard Wi-Fi connection QR string:
    WIFI:T:WPA;S:MyNetwork;P:MyPassword;H:false;;
    """
    if not ssid:
        raise ValueError("SSID cannot be empty")
    h_str = "true" if hidden else "false"
    # Escape special characters
    clean_ssid = ssid.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace(":", "\\:")
    clean_pw = password.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace(":", "\\:")
    return f"WIFI:T:{auth_type};S:{clean_ssid};P:{clean_pw};H:{h_str};;"


def generate_qr_image(
    data: str,
    fill_color: str = "#000000",
    back_color: str = "#ffffff",
    box_size: int = 10,
    border: int = 2,
    error_correction: str = "M",
    output_format: str = "png"
) -> bytes:
    """
    Generate QR code as raw bytes (PNG or SVG).
    """
    if not data or not data.strip():
        raise QRStudioError("QR code data cannot be empty.")

    ec = ERROR_CORRECTION_MAP.get(error_correction.upper(), qrcode.constants.ERROR_CORRECT_M)

    if output_format.lower() == "svg":
        qr = qrcode.QRCode(
            version=None,
            error_correction=ec,
            box_size=box_size,
            border=border,
            image_factory=qrcode.image.svg.SvgPathImage
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image()
        buf = io.BytesIO()
        img.save(buf)
        return buf.getvalue()

    # PNG Output
    qr = qrcode.QRCode(
        version=None,
        error_correction=ec,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Validate colors
    try:
        ImageColor.getrgb(fill_color)
    except Exception:
        fill_color = "#000000"

    try:
        ImageColor.getrgb(back_color)
    except Exception:
        back_color = "#ffffff"

    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_qr_base64(
    data: str,
    fill_color: str = "#000000",
    back_color: str = "#ffffff",
    box_size: int = 10,
    border: int = 2,
    error_correction: str = "M"
) -> str:
    """
    Returns data URI string for direct inline browser display:
    data:image/png;base64,...
    """
    png_bytes = generate_qr_image(
        data=data,
        fill_color=fill_color,
        back_color=back_color,
        box_size=box_size,
        border=border,
        error_correction=error_correction,
        output_format="png"
    )
    encoded = base64.b64encode(png_bytes).decode("utf-8")
    return f"data:image/png;base64,{encoded}"
