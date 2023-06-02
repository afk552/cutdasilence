import os
import math
import multiprocessing
from moviepy.editor import AudioClip, VideoFileClip, concatenate_videoclips
import PySimpleGUI as sg


def new_window(window):
    if window is not None:
        window.close(),

    working_directory = os.getcwd()
    vol_threshold = [
        0.05,
        0.1,
        0.15,
        0.20,
        0.25,
        0.30,
        0.35,
        0.40,
        0.45,
        0.50,
        0.55,
        0.60,
        0.65,
        0.70,
        0.75,
        0.80,
        0.85,
        0.90,
        0.95,
    ]

    x264_presets = [
        "ultrafast",
        "superfast",
        "veryfast",
        "faster",
        "fast",
        "medium",
        "slow",
        "slower",
        "veryslow",
        "placebo",
    ]

    style_size = {"size": (20, 20)}

    layout = [
        [sg.Text("Исходный файл:")],
        [
            sg.InputText(key="-FILE_PATH-", readonly=True),
            sg.FileBrowse(
                initial_folder=working_directory,
                file_types=[("Видеофайл", "*.mp4")],
                button_text="Выбрать",
            ),
        ],
        [
            sg.Text("Порог громкости"),
            sg.Slider(
                range=(0.01, 0.95),
                resolution=0.01,
                default_value=0.10,
                orientation="horizontal",
                enable_events=True,
                key="slider_vol_threshold",
            ),
        ],
        [
            sg.Text("Размер интервалов поиска тишины (сек.)"),
            sg.Combo(
                vol_threshold,
                default_value=vol_threshold[1],
                enable_events=True,
                readonly=True,
                key="combo_silent_interval",
                **style_size,
            ),
        ],
        [
            sg.Text("Количество тишины между интервалами разговора (сек.)"),
            sg.InputText(default_text="0.20", key="textbox_ease_in", **style_size),
        ],
        [
            sg.Text("Пресет кодирования:"),
            sg.Combo(
                x264_presets,
                default_value=x264_presets[0],
                enable_events=True,
                readonly=True,
                key="combo_encoding_preset",
                **style_size,
            ),
        ],
        [sg.Button("Загрузить")],
    ]
    sg.theme()
    return sg.Window(
        "CutDaSilence",
        layout,
        finalize=True,
        resizable=False,
        auto_size_text=True,
        element_justification="center",
        icon="gi.ico",
    )


def find_speaking_intervals(
    audio_clip, silence_chunk_size=0.1, volume_threshold=0.15, silence_between=0.25
):
    # Ищем тихие интервалы указанного размера
    chunks_amount = math.floor(audio_clip.end / silence_chunk_size)
    silent_intervals = []
    for i in range(chunks_amount):
        s = audio_clip.subclip(i * silence_chunk_size, (i + 1) * silence_chunk_size)
        v = s.max_volume()
        silent_intervals.append(v < volume_threshold)

    # Ищем интервалы разговора
    speaking_start, speaking_end = 0, 0
    speaking_intervals = []
    for i in range(1, len(silent_intervals)):
        e1 = silent_intervals[i - 1]
        e2 = silent_intervals[i]
        # Если конец разговора и найдена тишина -> вставляем тишину
        if e1 and not e2:
            speaking_start = i * silence_chunk_size
        if not e1 and e2:
            speaking_end = i * silence_chunk_size
            new_speaking_interval = [
                speaking_start - silence_between,
                speaking_end + silence_between,
            ]
            speaking_intervals.append(new_speaking_interval)
    return speaking_intervals


def main():
    sg.theme("SystemDefault1")
    # sg.theme("Black")
    window = new_window(None)

    while True:
        event, values = window.read()
        # print(event, values)

        match event:
            case "Загрузить":
                file_in = values["-FILE_PATH-"]
                try:
                    vid = VideoFileClip(file_in)
                except OSError:
                    sg.popup("Некорректный файл!")
                    continue

                foldername = sg.PopupGetFolder(
                    "Выберите папку для сохранения", no_window=True
                )
                if foldername:
                    filename = sg.popup_get_text("Введите имя файла")
                    file_out = os.path.join(
                        foldername, filename + os.path.splitext(file_in)[1]
                    )

                    intervals_to_keep = find_speaking_intervals(
                        vid.audio,
                        float(values["combo_silent_interval"]),
                        float(values["slider_vol_threshold"]),
                        float(values["textbox_ease_in"]),
                    )
                    keep_clips = [
                        vid.subclip(start, end)
                        for [start, end] in intervals_to_keep
                    ]
                    edited_video = concatenate_videoclips(keep_clips)
                    edited_video.write_videofile(
                        file_out,
                        fps=vid.fps,
                        preset=values["combo_encoding_preset"],
                        codec="libx264",
                        temp_audiofile="temp.m4a",
                        remove_temp=True,
                        audio_codec="aac",
                        threads=multiprocessing.cpu_count() / 2,
                    )
                    vid.close()
                    os.startfile(file_out)

        if event == sg.WIN_CLOSED or event == "Exit":
            break

    window.close()


if __name__ == "__main__":
    main()
