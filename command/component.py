"""
Main driver for the selection menu, using questionary library
"""
import questionary


class BulletMenu:
    """
    A CLI menu to select a choice from a list of choices using questionary.
    """

    def __init__(self, prompt: str = None, choices: dict[str, str] = None):
        self.prompt = prompt
        self.choices = list(choices.keys())
        self.descriptions = list(choices.values())



    def run(self, default_choice: int = 0) -> str:
        """Start the menu and return the selected choice"""

        rsp=questionary.select(
            self.prompt,
            choices=[
                questionary.Choice(
                    title=f"{choice:20}{self.descriptions[i]}",
                    value=choice
                ) for i, choice in enumerate(self.choices)
            ],
            instruction="↑↓ + Enter",
        ).ask()

        return rsp
