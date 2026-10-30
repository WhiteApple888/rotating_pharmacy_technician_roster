# Roster glossary

## Weekly rest day

For the weekly rest-day requirement, `RD`, `RD+`, `RD++`, and `VLRD` count
as rest days. Each roster week must contain exactly one.

## Rest-day spacing

For spacing, only `RD` and `VLRD` reset the count; `RD+` and `RD++` do not.
At most 12 days may fall between qualifying rest days: 12 is allowed and 13
is rejected. The check also accounts for the previous roster's rest day and
the trailing days at the end of the current roster. Every date in the
`lastRosterRD` sheet represents a qualifying `RD` or `VLRD`.
