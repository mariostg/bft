from django.core.management.base import BaseCommand

from bft.models import BftStatus


class UserInput(BaseCommand):

    def _get_user_input(self, hint: str) -> bool:
        _continue = False
        choice = input(f"Continue using {hint} ? [y/n] ")
        if not choice or choice in ("N", "n"):
            _continue = False
        if choice in ("Y", "y"):
            _continue = True
        return _continue

    def set_fy(self, fy=None) -> str | None:
        currentfy = BftStatus.current.fy()
        if not fy:
            msg = f"You did not specify a fiscal year. Current fiscal year [{currentfy}] will be used."
            self.stdout.write(style_func=self.style.WARNING, msg=msg)
            if self._get_user_input(currentfy):
                fy = currentfy
        else:
            if fy != currentfy:
                msg = f"You specified a FY different than current value.\nCurrent is {currentfy}.\nYou provided {fy}"
                self.stdout.write(style_func=self.style.WARNING, msg=msg)
                if not self._get_user_input(fy):
                    fy = None

        return fy

    def set_period(self, period=None) -> str | None:
        currentperiod = BftStatus.current.period()
        if not period:
            msg = f"You did not specify a period. Current period [{currentperiod}] will be used."
            self.stdout.write(style_func=self.style.WARNING, msg=msg)
            if self._get_user_input(currentperiod):
                period = currentperiod
        else:
            if period != currentperiod:
                msg = f"You specified a period different than current value.\nCurrent is {currentperiod}.\nYou provided {period}"
                self.stdout.write(style_func=self.style.WARNING, msg=msg)
                if not self._get_user_input(period):
                    period = None
        return period
