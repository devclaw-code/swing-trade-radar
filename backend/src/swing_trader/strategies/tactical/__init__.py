"""Tactical Swings — short-term (1\u20135 day hold) screener engine.

Distinct from the v2 "Core" verdict strategies (30-day trend holds), tactical
setups are fast mean-reversion / breakout plays. Each setup is a self-contained
``TacticalStrategy`` returning a ``TacticalResult`` so adding a 3rd or 4th setup
is just one new file + one registry line in ``engine.tactical_engine``.

Shared contract:
  * Regime filter for every tactical setup: ``Price > 200 SMA``.
  * Risk geometry flows through ``engine.risk_levels.dynamic_atr_trade``
    (1.5 * ATR stop, min 2.0 R:R) unless a setup defines structural levels.
"""
