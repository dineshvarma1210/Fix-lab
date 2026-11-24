# FIX Hands-On Lab — two QuickFIX engines on your laptop

You asked to get hands-on before the follow-up. This is a real FIX 4.4 session
running on localhost: one engine plays the venue (acceptor), one plays your app
(initiator). I ran this exact setup and verified all three experiments below.

## Files

- `executor.py` + `acceptor.cfg` — the venue. Listens on 127.0.0.1:9876, acks every
  order (ExecutionReport New) then fills it completely (Trade/Filled).
- `tradeclient.py` + `initiator.cfg` — your app. Logs on, sends one NewOrderSingle
  (BUY 100 AAPL @ 150.00 limit), prints every ExecutionReport.
- Both use file stores (`store-acceptor/`, `store-initiator/`), so sequence numbers
  survive restarts — that is what makes experiment 3 work. `ResetOnLogon=N` in
  both configs: sequence numbers are never reset on reconnect.

## Setup (once)

Needs Python 3.10+. In this folder:

```
python3 -m venv venv
venv/bin/pip install quickfix
```

On Windows use `venv\Scripts\pip install quickfix` and `venv\Scripts\python` below.
The first install can take several minutes — it compiles the C++ engine. That is
normal.

## Run

Terminal 1 (venue):

```
venv/bin/python -u executor.py acceptor.cfg
```

Terminal 2 (your app):

```
venv/bin/python -u tradeclient.py initiator.cfg ORDER-1
```

Use `python -u` (unbuffered) or the output will not appear until the process ends.
To send another order, restart the client with a new ID: `ORDER-2`, `ORDER-3`...

## Experiment 1 — the order flow

Watch terminal 2. You will see, in order:

1. Logon both ways (`35=A`, sequence number 1 each side).
2. `35=D` NewOrderSingle out: `11=ORDER-1|55=AAPL|54=1|38=100|40=2|44=150`.
3. `35=8` ExecutionReport ack: `150=0` (New), `39=0`, `14=0` (CumQty), `151=100` (LeavesQty).
4. One second later, `35=8` fill: `150=F` (Trade), `39=2` (Filled), `14=100`, `151=0`.

That is the whole order lifecycle from your prep file, on the wire.

## Experiment 2 — restart, sequence numbers continue

Stop the client (Ctrl-C) and start it again with a new order ID. The Logon goes
out with the next sequence number (3, then 4...), not 1. Nothing is reset. That
is `ResetOnLogon=N` plus the file store doing its job — the session resumes
exactly where it left off.

## Experiment 3 — kill mid-flight, watch the recovery

This is interview question 2, live. Start the client with `ORDER-3`, kill it
within a second (after the ack, before the fill), then restart it with `ORDER-4`.
What you will see on restart:

1. Logon with the continued sequence number.
2. The venue's Logon arrives with a higher sequence number than you expect —
   a gap. Your client sends `35=2` ResendRequest for the missing range.
3. The venue replays the missed fill: ExecutionReport with `43=Y` (PossDupFlag)
   and `122=` (OrigSendingTime — the original send time, proving it is a replay,
   not a new fill).
4. A `35=4` SequenceReset with `123=Y` (GapFillFlag) skips the admin message.
5. Then ORDER-4's ack and fill arrive normally.

If you ever get asked "how do you know the fill wasn't applied twice?" — this
is the answer: `43=Y` plus dedupe on `ClOrdID` + `ExecID`.

## Where the logs live

QuickFIX writes message logs to `log-acceptor/` and `log-initiator/`
(`FIX.4.4-...messages.current.log`, `|` in place of the SOH separator).
The `.body` / `.seqnums` files under `store-*/` are the persisted sequence
numbers. Delete the `store-*` folders to start numbering from 1 again.

## If it does not start

- "Connection refused": terminal 1 (the venue) is not running yet. Start it first.
- `pip install quickfix` fails on Windows: install Microsoft C++ Build Tools,
  then retry. On Mac/Linux it usually builds cleanly.
- Sessions only log on between StartTime and EndTime in the configs — both are
  set to the full day, so this should not bite you.
