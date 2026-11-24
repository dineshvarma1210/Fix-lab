"""FIX initiator (the 'app'). Connects to the acceptor on 127.0.0.1:9876,
logs on, sends ONE NewOrderSingle (buy 100 AAPL @ 150.00 limit),
prints every ExecutionReport it gets back.

Run:  python tradeclient.py initiator.cfg
"""
import sys
import time
import quickfix as fix


class TradeClient(fix.Application):
    order_sent = False

    def onCreate(self, sessionID):
        print("[client] session created:", sessionID)

    def onLogon(self, sessionID):
        print("[client] LOGON:", sessionID)
        if not TradeClient.order_sent:
            self.send_order(sessionID)
            TradeClient.order_sent = True

    def onLogout(self, sessionID):
        print("[client] LOGOUT:", sessionID)

    def toAdmin(self, message, sessionID):
        pass

    def fromAdmin(self, message, sessionID):
        print("[client] admin in: ", message.toString().replace("\x01", "|"))

    def toApp(self, message, sessionID):
        print("[client] app out:", message.toString().replace("\x01", "|"))

    def fromApp(self, message, sessionID):
        print("[client] app in: ", message.toString().replace("\x01", "|"))

    def send_order(self, sessionID):
        clOrdID = sys.argv[2] if len(sys.argv) > 2 else "ORDER-1"
        order = fix.Message()
        order.getHeader().setField(fix.MsgType(fix.MsgType_NewOrderSingle))
        order.setField(fix.ClOrdID(clOrdID))
        order.setField(fix.HandlInst('1'))          # automated execution
        order.setField(fix.Symbol("AAPL"))
        order.setField(fix.Side(fix.Side_BUY))
        order.setField(fix.TransactTime())
        order.setField(fix.OrdType(fix.OrdType_LIMIT))
        order.setField(fix.OrderQty(100))
        order.setField(fix.Price(150.00))
        fix.Session.sendToTarget(order, sessionID)
        print("[client] sent NewOrderSingle: BUY 100 AAPL @ 150.00 limit")


if __name__ == "__main__":
    settings = fix.SessionSettings(sys.argv[1])
    application = TradeClient()
    storeFactory = fix.FileStoreFactory(settings)
    logFactory = fix.FileLogFactory(settings)
    initiator = fix.SocketInitiator(application, storeFactory, settings, logFactory)
    initiator.start()
    print("[client] connecting to 127.0.0.1:9876. Ctrl-C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        initiator.stop()
