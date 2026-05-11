from pathlib import Path
import base64

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio"
AUDIO_BASE64_DIR = BASE_DIR / "audio_base64"

AUDIO_FILENAMES = [
    "Glass.aiff",
    "测耳温.mp3",
    "称体重.mp3",
    "请设置好红外摄像机.mp3",
    "请设置好红外摄像机和走步机控制器.mp3",
    "请准备好K5、面罩和绑带,并设置程序.mp3",
]


def _read_audio_text(filename: str) -> str:
    single_file = AUDIO_BASE64_DIR / f"{filename}.base64"
    split_files = sorted(AUDIO_BASE64_DIR.glob(f"{filename}.part*.base64"))

    if single_file.exists():
        return single_file.read_text(encoding="utf-8")

    if split_files:
        return "".join(item.read_text(encoding="utf-8") for item in split_files)

    raise FileNotFoundError(f"找不到音频文本文件: {filename}")


def restore_audio_files():
    AUDIO_DIR.mkdir(exist_ok=True)

    for filename in AUDIO_FILENAMES:
        output_file = AUDIO_DIR / filename
        if output_file.exists() and output_file.stat().st_size > 0:
            continue

        try:
            text_data = _read_audio_text(filename)
            cleaned_text = "".join(text_data.split())
            audio_bytes = base64.b64decode(cleaned_text)
            output_file.write_bytes(audio_bytes)
            print(f"已恢复音频文件: {output_file}")
        except Exception as error:
            print(f"恢复音频失败: {filename}，错误: {error}")
