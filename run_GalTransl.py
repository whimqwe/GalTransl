import os
import sys

# 基本配置，避免循环导入
from GalTransl import (
    CONFIG_FILENAME,
    PROGRAM_SPLASH,
    TRANSLATOR_SUPPORTED
)
from GalTransl.i18n import get_text,GT_LANG


# Get input prompt based on language
def get_input_prompt():
    return get_text("input_project_path", GT_LANG)


class ProjectManager:
    def __init__(self):
        self.user_input = ""
        self.project_dir = ""
        self.config_file_name = CONFIG_FILENAME
        self.translator = ""

    def validate_project_path(self, user_input: str) -> tuple[str | None, str | None, str | None]:
        if not user_input or not isinstance(user_input, str):
            print(get_text("input_path_empty", GT_LANG))
            return None, None, None
        try:
            user_input = os.path.abspath(user_input)
            if user_input.endswith(".yaml"):
                config_file_name = os.path.basename(user_input)
                project_dir = os.path.dirname(user_input)
            else:
                config_file_name = CONFIG_FILENAME
                project_dir = user_input

            if not os.path.exists(project_dir):
                print(get_text("project_folder_not_exist", GT_LANG, project_dir))
                return None, None, None

            config_path = os.path.join(project_dir, config_file_name)
            if not os.path.exists(config_path):
                print(get_text("config_file_not_exist", GT_LANG, config_path))
                return None, None, None

            if not os.path.isfile(config_path):
                print(get_text("config_file_not_valid", GT_LANG, config_path))
                return None, None, None

            return user_input, project_dir, config_file_name
        except Exception as e:
            print(get_text("error_validating_path", GT_LANG, str(e)))
            return None, None, None

    def get_user_input(self):
        while True:
            input_prompt = get_text("input_project_path", GT_LANG).replace(
                "[default]",
                get_text("continue_with_project", GT_LANG, self.project_name()) if self.project_dir else "",
            )
            user_input = input(input_prompt).strip('"') or self.user_input

            if not user_input:
                continue
            
            user_input = user_input.strip('"').strip("'")
            self.user_input, self.project_dir, self.config_file_name = (
                self.validate_project_path(user_input)
            )
            if not self.project_dir:
                continue

            return

    def print_program_info(self):
        from GalTransl import GALTRANSL_VERSION, AUTHOR, CONTRIBUTORS
        print(PROGRAM_SPLASH)
        print(f"Ver: {GALTRANSL_VERSION}")
        print(f"Author: {AUTHOR}")
        print(f"Contributors: {CONTRIBUTORS}\n")

    def choose_translator(self):
        from command import BulletMenu
        
        default_choice = (
            list(TRANSLATOR_SUPPORTED.keys()).index(self.translator)
            if self.translator
            else 0
        )
        os.system("")  # 解决cmd的ANSI转义bug
        translators_dic={x:y[GT_LANG] for x,y in TRANSLATOR_SUPPORTED.items()}
        self.translator = BulletMenu(
            get_text("select_translator",GT_LANG, self.project_name()), translators_dic
        ).run(default_choice)

    def project_name(self):
        return self.project_dir.split(os.sep)[-1] if self.project_dir else ""

    def create_shortcut_win(self) -> None:
        try:
            from GalTransl import GALTRANSL_VERSION
            TEMPLATE = '@echo off\nchcp 65001\nset "CURRENT_PATH=%CD%"\ncd /d "{0}"\nset "GT_LANG={4}"\n{1} "{2}" {3}\npause\ncd /d "%CURRENT_PATH%"'
            run_com = "python.exe " + os.path.basename(__file__)
            program_dir = os.path.dirname(os.path.abspath(__file__))
            shortcut_path = f"{self.project_dir}{os.sep}run_GalTransl_v{GALTRANSL_VERSION}_{self.translator}.bat"
            conf_path = "%CURRENT_PATH%\\" + self.config_file_name
            if "nt" not in os.name:  # not windows
                return
            if getattr(sys, "frozen", False):  # PyInstaller
                run_com = os.path.basename(sys.executable)
                program_dir = os.path.dirname(sys.executable)
            with open(shortcut_path, "w", encoding="utf-8") as f:
                text = TEMPLATE.format(program_dir, run_com, conf_path, self.translator, GT_LANG)
                f.write(text)
        except Exception as e:
            print(get_text("error_creating_shortcut", GT_LANG, str(e)))

    def run(self):
        # 检查命令行参数
        if len(sys.argv) > 1:
            self.user_input = sys.argv[1]
            self.user_input, self.project_dir, self.config_file_name = (
                self.validate_project_path(self.user_input)
            )
            if len(sys.argv) > 2 and sys.argv[2] in TRANSLATOR_SUPPORTED.keys():
                self.translator = sys.argv[2]

        while True:
            self.print_program_info()

            # 如果初始路径无效或未提供，进入交互式输入阶段
            if not self.project_dir:
                try:
                    self.get_user_input()
                except KeyboardInterrupt:
                    print("\nGoodbye.")
                    return
            if not self.translator:
                try:
                    self.choose_translator()
                except KeyboardInterrupt:
                    print("\nGoodbye.")
                    return
            if self.translator not in ["show-plugs", "dump-name"]:
                self.create_shortcut_win()
            from GalTransl.__main__ import worker
            worker(
                self.project_dir,
                self.config_file_name,
                self.translator,
                show_banner=False
            )

            print(get_text("translation_completed", GT_LANG))
            self.user_input = ""
            self.translator = ""

            os.system("pause")
            os.system("cls")


if __name__ == "__main__":
    manager = ProjectManager()
    manager.run()
