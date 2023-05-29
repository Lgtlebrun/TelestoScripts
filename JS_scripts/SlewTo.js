/* Java Script */

var ErrorMsg;

/* slew to the given target */

function slew() {
    var Mount = sky6RASCOMTele;
    var TargetRA, TargetDec;

    /* no error yet */
    ErrorMsg = "";

    /* wait for mount operations to complete */
    Mount.Asynchronous = false;

    /* connect to the mount, if we're not already connected */
    if (Mount.IsConnected)
        ;
    else {
        try {
            Mount.Connect();
        }
        catch (connerr) {
            ErrorMsg = "Mount not connected:  " + connerr.message;
            return false;
        }
    }

    /* set up the destination coordinates (approximate location of M 42) */
    TargetRA = $0;
    TargetDec = $1;

    /* and slew to the target */
    Mount.LastSlewError = 0;
    try {
        Mount.SlewToRaDec(TargetRA, TargetDec, "");
    }
    catch (slewerr) {
        ErrorMsg = "Slew failed:  " + slewerr.message;
        return false;
    }

    /* no error */
    return true;
}

if (slew())
    "Success!";
else
    ErrorMsg;