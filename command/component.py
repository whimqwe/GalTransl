"""Main driver for the selection menu, using InquirerPy library"""
from InquirerPy import inquirer
from InquirerPy.base.control import Choice


class BulletMenu:
    """
    A CLI menu to select a choice from a list of choices using InquirerPy.
    """

    def __init__(self, prompt: str = None, choices: dict[str, str] = None):
        self.prompt = prompt
        self.choices = list(choices.keys())
        self.descriptions = list(choices.values())

    def run(self, default_choice: int = 0) -> str:
        """Start the menu and return the selected choice"""

        rsp = inquirer.select(
            message=self.prompt,
            choices=[
                Choice(
                    name=f"{choice:20}{self.descriptions[i]}",
                    value=choice
                ) for i, choice in enumerate(self.choices)
            ],
            instruction="↑↓ + Enter",
            default=self.choices[default_choice] if self.choices else None
        ).execute()

        return rsp
