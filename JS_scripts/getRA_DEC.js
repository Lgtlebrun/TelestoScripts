/* Java Script */

var target = "$0";
var currentRa = "";
var currentDec = "";

sky6RASCOMTele.Connect();
sky6StarChart.Refresh();

if (target == "None"){

    sky6RASCOMTele.GetRaDec();
    currentRa = sky6RASCOMTele.dRa;
    currentDec = sky6RASCOMTele.dDec;

}

else{
    sky6StarChart.Find(target);
    sky6ObjectInformation.Property(54);
    currentRa = sky6ObjectInformation.ObjInfoPropOut;
    sky6ObjectInformation.Property(55);
    currentDec = sky6ObjectInformation.ObjInfoPropOut;
}

out = String(currentRa) + '&' + String(currentDec);