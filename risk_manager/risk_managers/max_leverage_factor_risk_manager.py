from decimal import Decimal
import MetaTrader5 as mt5
from events.events import SizingEvent
from risk_manager.interfaces.risk_manager_interface import IRiskManager
from risk_manager.properties.risk_manager_properties import MaxLeverageFactorRiskProps


class MaxLeverageFactorRiskManager(IRiskManager):
    def __init__(self, properties: MaxLeverageFactorRiskProps) -> None:
        self.max_leverage_factor = properties.max_leverage_factor

    def _compute_leverage_factor(self, account_value_acc_ccy: Decimal) -> Decimal:
        account_equity = Decimal(mt5.account_info().equity)  # type: ignore

        if account_equity <= Decimal(0):
            return Decimal("Inf")
        return account_value_acc_ccy / account_equity

    def _check_expected_new_position_is_compliant_with_max_leverage_factor(
        self,
        sizing_event: SizingEvent,
        current_positions_value_acc_ccy: Decimal,
        new_position_value_acc_ccy: Decimal,
    ) -> bool:
        # Calculate expected account value if the new position is executed
        new_account_value = current_positions_value_acc_ccy + new_position_value_acc_ccy

        # Calculate the new leverage factor if WE EXECUTED the new position
        new_leverage_factor = self._compute_leverage_factor(new_account_value)

        # Check if the new leverage factor is compliant with the max leverage factor
        if abs(new_leverage_factor) <= self.max_leverage_factor:
            return True
        print(
            f"RISK MGMT: The objective position {sizing_event.signal} {sizing_event.volume} implies a Leverage Factor of {abs(new_leverage_factor):.2f} which is higher than the max leverage factor {self.max_leverage_factor}"
        )
        return False

    def assess_order(  # type: ignore
        self,
        sizing_event: SizingEvent,
        current_positions_value_acc_ccy: Decimal,
        new_position_value_acc_ccy: Decimal,
    ) -> Decimal:
        # This is like a disco doorman -> it lets the op pass

        if (
            self._check_expected_new_position_is_compliant_with_max_leverage_factor(
                sizing_event=sizing_event,
                current_positions_value_acc_ccy=current_positions_value_acc_ccy,
                new_position_value_acc_ccy=new_position_value_acc_ccy,
            )
            < self.max_leverage_factor
        ):
            return Decimal(sizing_event.volume)

        return Decimal(0)
