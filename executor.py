"""FIX acceptor (the 'venue'). Listens on 9876, acks every NewOrderSingle
with an ExecutionReport (New), then fills it completely (Trade/Filled).

Run:  python executor.py acceptor.cfg
"""
import sys
import time
import quickfix as fix


class Executor(fix.Application):
    def onCreate(self, sessionID):
        print("[acceptor] session created:", sessionID)

    def onLogon(self, sessionID):
        print("[acceptor] LOGON:", sessionID)

    def onLogout(self, sessionID):
        print("[acceptor] LOGOUT:", sessionID)

    def toAdmin(self, message, sessionID):
        pass

    def fromAdmin(self, message, sessionID):
        print("[acceptor] admin in: ", message.toString().replace("\x01", "|"))

    def toApp(self, message, sessionID):
        print("[acceptor] app out:", message.toString().replace("\x01", "|"))

    def fromApp(self, message, sessionID):
        print("[acceptor] app in: ", message.toString().replace("\x01", "|"))
        msgType = fix.MsgType()
        message.getHeader().getField(msgType)
        if msgType.getValue() == fix.MsgType_NewOrderSingle:
            self.handle_new_order(message, sessionID)

    def handle_new_order(self, message, sessionID):
        clOrdID = fix.ClOrdID()
        symbol = fix.Symbol()
        side = fix.Side()
        orderQty = fix.OrderQty()
        price = fix.Price()
        message.getField(clOrdID)
        message.getField(symbol)
        message.getField(side)
        message.getField(orderQty)
        message.getField(price)
        qty = float(orderQty.getValue())
        px = float(price.getValue())

        # 1) Ack: ExecType=New (0), OrdStatus=New (0)
        ack = fix.Message()
        ack.getHeader().setField(fix.MsgType(fix.MsgType_ExecutionReport))
        ack.setField(fix.OrderID("V-1001"))
        ack.setField(fix.ExecID("E-1"))
        ack.setField(fix.ExecType(fix.ExecType_NEW))
        ack.setField(fix.OrdStatus(fix.OrdStatus_NEW))
        ack.setField(fix.Symbol(symbol.getValue()))
        ack.setField(fix.Side(side.getValue()))
        ack.setField(fix.LeavesQty(qty))
        ack.setField(fix.CumQty(0))
        ack.setField(fix.AvgPx(0))
        ack.setField(clOrdID)
        fix.Session.sendToTarget(ack, sessionID)
        print("[acceptor] sent ack (New)")

        # 2) Fill: ExecType=Trade (F), OrdStatus=Filled (2)
        time.sleep(1)
        fill = fix.Message()
        fill.getHeader().setField(fix.MsgType(fix.MsgType_ExecutionReport))
        fill.setField(fix.OrderID("V-1001"))
        fill.setField(fix.ExecID("E-2"))
        fill.setField(fix.ExecType(fix.ExecType_TRADE))
        fill.setField(fix.OrdStatus(fix.OrdStatus_FILLED))
        fill.setField(fix.Symbol(symbol.getValue()))
        fill.setField(fix.Side(side.getValue()))
        fill.setField(fix.LeavesQty(0))
        fill.setField(fix.CumQty(qty))
        fill.setField(fix.AvgPx(px))
        fill.setField(fix.LastQty(qty))
        fill.setField(fix.LastPx(px))
        fill.setField(clOrdID)
        fix.Session.sendToTarget(fill, sessionID)
        print("[acceptor] sent fill (Trade/Filled)")


if __name__ == "__main__":
    settings = fix.SessionSettings(sys.argv[1])
    application = Executor()
    storeFactory = fix.FileStoreFactory(settings)
    logFactory = fix.FileLogFactory(settings)
    acceptor = fix.SocketAcceptor(application, storeFactory, settings, logFactory)
    acceptor.start()
    print("[acceptor] listening on 9876. Ctrl-C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        acceptor.stop()
