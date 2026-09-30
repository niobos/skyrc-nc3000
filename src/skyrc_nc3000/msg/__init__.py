from . import curve, msg06, msg57, msg96, status

dispatch = {
    0x06: msg06.Msg06Response,
    0x57: msg57.Msg57Response,
    0x96: msg96.Msg96Response,
    0x98: curve.CurveMsg,
    0x9a: status.StatusResponse,
}
