<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
  <NamedLayer><Name>CDP_DEMIRYOLU</Name><UserStyle><Title>CDP_DEMIRYOLU</Title><FeatureTypeStyle>
    <Rule><Name>0</Name><Title>DEMIRYOLU</Title><MaxScaleDenominator>500000</MaxScaleDenominator>
      <ogc:Filter><ogc:PropertyIsEqualTo><ogc:PropertyName>DemirTip</ogc:PropertyName><ogc:Literal>Demiryolu</ogc:Literal></ogc:PropertyIsEqualTo></ogc:Filter>
      <LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre"><Stroke><GraphicStroke><Graphic><Mark><WellKnownName>ttf://UIP_10_1#0x0058</WellKnownName><Fill><CssParameter name="fill">#000000</CssParameter></Fill><Stroke><CssParameter name="stroke-opacity">0</CssParameter><CssParameter name="stroke">#000000</CssParameter><CssParameter name="stroke-width">1</CssParameter></Stroke></Mark><Size>15</Size></Graphic></GraphicStroke></Stroke></LineSymbolizer>
    </Rule>
    <Rule><Name>0</Name><Title>HIZLI_TREN_HATTI</Title><MaxScaleDenominator>500000</MaxScaleDenominator>
      <ogc:Filter><ogc:PropertyIsEqualTo><ogc:PropertyName>DemirTip</ogc:PropertyName><ogc:Literal>HizliTrenHatti</ogc:Literal></ogc:PropertyIsEqualTo></ogc:Filter>
      <LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre"><Stroke><GraphicStroke><Graphic><Mark><WellKnownName>ttf://UIP_10_3#0x002f</WellKnownName><Fill><CssParameter name="fill">#000000</CssParameter></Fill><Stroke><CssParameter name="stroke-opacity">0</CssParameter><CssParameter name="stroke">#000000</CssParameter><CssParameter name="stroke-width">1</CssParameter></Stroke></Mark><Size>15</Size></Graphic></GraphicStroke></Stroke></LineSymbolizer>
    </Rule>
    <Rule><Name>rail-500000-100000</Name><Title>RAYLI_TOPLU_TASIMA_GUZERGAHI - uzak olcek</Title><MaxScaleDenominator>500000</MaxScaleDenominator><MinScaleDenominator>100000</MinScaleDenominator>
      <ogc:Filter><ogc:PropertyIsEqualTo><ogc:PropertyName>DemirTip</ogc:PropertyName><ogc:Literal>RayliTopluTasimaGuzergahi</ogc:Literal></ogc:PropertyIsEqualTo></ogc:Filter>
      <LineSymbolizer><Stroke><GraphicStroke><Graphic><Mark><WellKnownName>ttf://UIP_10_3#0x0061</WellKnownName><Fill><CssParameter name="fill">#000000</CssParameter></Fill><Stroke><CssParameter name="stroke-opacity">0</CssParameter><CssParameter name="stroke">#000000</CssParameter><CssParameter name="stroke-width">1</CssParameter></Stroke></Mark><Size>10</Size></Graphic></GraphicStroke></Stroke></LineSymbolizer>
    </Rule>
    <Rule><Name>rail-100000-25000</Name><Title>RAYLI_TOPLU_TASIMA_GUZERGAHI - orta olcek</Title><MaxScaleDenominator>100000</MaxScaleDenominator><MinScaleDenominator>25000</MinScaleDenominator>
      <ogc:Filter><ogc:PropertyIsEqualTo><ogc:PropertyName>DemirTip</ogc:PropertyName><ogc:Literal>RayliTopluTasimaGuzergahi</ogc:Literal></ogc:PropertyIsEqualTo></ogc:Filter>
      <LineSymbolizer><Stroke><GraphicStroke><Graphic><Mark><WellKnownName>ttf://UIP_10_3#0x0061</WellKnownName><Fill><CssParameter name="fill">#000000</CssParameter></Fill><Stroke><CssParameter name="stroke-opacity">0</CssParameter><CssParameter name="stroke">#000000</CssParameter><CssParameter name="stroke-width">1</CssParameter></Stroke></Mark><Size>16</Size></Graphic></GraphicStroke></Stroke></LineSymbolizer>
    </Rule>
    <Rule><Name>rail-25000-5000</Name><Title>RAYLI_TOPLU_TASIMA_GUZERGAHI - yakin olcek</Title><MaxScaleDenominator>25000</MaxScaleDenominator><MinScaleDenominator>5000</MinScaleDenominator>
      <ogc:Filter><ogc:PropertyIsEqualTo><ogc:PropertyName>DemirTip</ogc:PropertyName><ogc:Literal>RayliTopluTasimaGuzergahi</ogc:Literal></ogc:PropertyIsEqualTo></ogc:Filter>
      <LineSymbolizer><Stroke><GraphicStroke><Graphic><Mark><WellKnownName>ttf://UIP_10_3#0x0061</WellKnownName><Fill><CssParameter name="fill">#000000</CssParameter></Fill><Stroke><CssParameter name="stroke-opacity">0</CssParameter><CssParameter name="stroke">#000000</CssParameter><CssParameter name="stroke-width">1</CssParameter></Stroke></Mark><Size>24</Size></Graphic></GraphicStroke></Stroke></LineSymbolizer>
    </Rule>
    <Rule><Name>rail-5000</Name><Title>RAYLI_TOPLU_TASIMA_GUZERGAHI - cok yakin olcek</Title><MaxScaleDenominator>5000</MaxScaleDenominator>
      <ogc:Filter><ogc:PropertyIsEqualTo><ogc:PropertyName>DemirTip</ogc:PropertyName><ogc:Literal>RayliTopluTasimaGuzergahi</ogc:Literal></ogc:PropertyIsEqualTo></ogc:Filter>
      <LineSymbolizer><Stroke><GraphicStroke><Graphic><Mark><WellKnownName>ttf://UIP_10_3#0x0061</WellKnownName><Fill><CssParameter name="fill">#000000</CssParameter></Fill><Stroke><CssParameter name="stroke-opacity">0</CssParameter><CssParameter name="stroke">#000000</CssParameter><CssParameter name="stroke-width">1</CssParameter></Stroke></Mark><Size>34</Size></Graphic></GraphicStroke></Stroke></LineSymbolizer>
    </Rule>
  </FeatureTypeStyle></UserStyle></NamedLayer>
</StyledLayerDescriptor>