/* Java Script */

celObj = "$0";
start = false;


sky6StarChart.Refresh()
sky6StarChart.Find(celObj);
sky6ObjectInformation.Property(59);
alt = sky6ObjectInformation.ObjInfoPropOut;

if alt > 0 {start = true;}


out = start;