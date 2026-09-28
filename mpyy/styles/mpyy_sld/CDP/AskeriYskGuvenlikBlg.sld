<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>CDP_ASKERI_YSK_GUVENLIK_BLG</Name>
    <UserStyle>
      <Title>CDP_ASKERI_YSK_GUVENLIK_BLG</Title>
      <FeatureTypeStyle>
        <Rule>
          <Name>askeri-yasak-bolge</Name>
          <Title>ASKERI YASAK BOLGE</Title>
          <MaxScaleDenominator>500000</MaxScaleDenominator>
          <ogc:Filter><ogc:Or>
            <ogc:PropertyIsEqualTo><ogc:PropertyName>AskeriBolgeTip</ogc:PropertyName><ogc:Literal>AskeriYasakBolge</ogc:Literal></ogc:PropertyIsEqualTo>
            <ogc:PropertyIsEqualTo><ogc:PropertyName>AskeriBolgeTip</ogc:PropertyName><ogc:Literal>AskeriYasakBolge</ogc:Literal></ogc:PropertyIsEqualTo>
          </ogc:Or></ogc:Filter>
          <PolygonSymbolizer>
            <Fill><GraphicFill><Graphic><ExternalGraphic>
              <OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:f303e6f1-d070-4cd3-9f7c-266d7d9e5d84.png" />
              <Format>image/png</Format>
            </ExternalGraphic></Graphic></GraphicFill></Fill>
          </PolygonSymbolizer>
          <PointSymbolizer><Graphic><ExternalGraphic>
            <OnlineResource xlink:type="simple" xlink:href="mpyy-eksik-sembol:AskeriAlan.svg" />
            <Format>image/svg</Format>
          </ExternalGraphic><Size>38</Size></Graphic></PointSymbolizer>
        </Rule>
        <Rule>
          <Name>askeri-yasak-ve-guvenlik-bolgesi</Name>
          <Title>ASKERI YASAK VE GUVENLIK BOLGESI</Title>
          <MaxScaleDenominator>500000</MaxScaleDenominator>
          <ogc:Filter><ogc:Or>
            <ogc:PropertyIsEqualTo><ogc:PropertyName>AskeriBolgeTip</ogc:PropertyName><ogc:Literal>AskeriYasakVeGuvenlikBolgesi</ogc:Literal></ogc:PropertyIsEqualTo>
            <ogc:PropertyIsEqualTo><ogc:PropertyName>AskeriBolgeTip</ogc:PropertyName><ogc:Literal>AskeriYasakVeGuvenlikBolgesi</ogc:Literal></ogc:PropertyIsEqualTo>
          </ogc:Or></ogc:Filter>
          <PolygonSymbolizer>
            <Fill><GraphicFill><Graphic><ExternalGraphic>
              <OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:f303e6f1-d070-4cd3-9f7c-266d7d9e5d84.png" />
              <Format>image/png</Format>
            </ExternalGraphic></Graphic></GraphicFill></Fill>
          </PolygonSymbolizer>
          <PointSymbolizer><Graphic><ExternalGraphic>
            <OnlineResource xlink:type="simple" xlink:href="mpyy-eksik-sembol:AskeriAlan.svg" />
            <Format>image/svg</Format>
          </ExternalGraphic><Size>38</Size></Graphic></PointSymbolizer>
          <LineSymbolizer>
            <Stroke><GraphicStroke><Graphic><Mark>
              <WellKnownName>wkt://MULTILINESTRING((-0.5 0,0.2 0),(0.2 -0.15,0.5 0.15),(0.2 0.15,0.5 -0.15),(-0.5 -0.5,-0.5 -0.5),(-0.5 0.5,-0.5 0.5))</WellKnownName>
              <Stroke><CssParameter name="stroke">#FF0000</CssParameter><CssParameter name="stroke-width">1.13</CssParameter><CssParameter name="stroke-linecap">butt</CssParameter><CssParameter name="stroke-linejoin">round</CssParameter></Stroke>
            </Mark><Size>37.8</Size></Graphic></GraphicStroke></Stroke>
            <VendorOption name="graphic-margin">0</VendorOption>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>guvenlik-bolgesi</Name>
          <Title>GUVENLIK BOLGESI</Title>
          <MaxScaleDenominator>500000</MaxScaleDenominator>
          <ogc:Filter><ogc:Or>
            <ogc:PropertyIsEqualTo><ogc:PropertyName>AskeriBolgeTip</ogc:PropertyName><ogc:Literal>GuvenlikBolgesi</ogc:Literal></ogc:PropertyIsEqualTo>
            <ogc:PropertyIsEqualTo><ogc:PropertyName>AskeriBolgeTip</ogc:PropertyName><ogc:Literal>GuvenlikBolgesi</ogc:Literal></ogc:PropertyIsEqualTo>
          </ogc:Or></ogc:Filter>
          <LineSymbolizer>
            <Stroke><GraphicStroke><Graphic><Mark>
              <WellKnownName>wkt://MULTILINESTRING((-0.5 0,0.2 0),(0.2 -0.15,0.5 0.15),(0.2 0.15,0.5 -0.15),(-0.5 -0.5,-0.5 -0.5),(-0.5 0.5,-0.5 0.5))</WellKnownName>
              <Stroke><CssParameter name="stroke">#FF0000</CssParameter><CssParameter name="stroke-width">1.13</CssParameter><CssParameter name="stroke-linecap">butt</CssParameter><CssParameter name="stroke-linejoin">round</CssParameter></Stroke>
            </Mark><Size>37.8</Size></Graphic></GraphicStroke></Stroke>
            <VendorOption name="graphic-margin">0</VendorOption>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>eski-kayit-uyumlulugu</Name>
          <Title>TIP BILGISI OLMAYAN ESKI ASKERI ALAN</Title>
          <MaxScaleDenominator>500000</MaxScaleDenominator>
          <ogc:ElseFilter />
          <PolygonSymbolizer>
            <Fill><GraphicFill><Graphic><ExternalGraphic>
              <OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:f303e6f1-d070-4cd3-9f7c-266d7d9e5d84.png" />
              <Format>image/png</Format>
            </ExternalGraphic></Graphic></GraphicFill></Fill>
          </PolygonSymbolizer>
          <PointSymbolizer><Graphic><ExternalGraphic>
            <OnlineResource xlink:type="simple" xlink:href="mpyy-eksik-sembol:AskeriAlan.svg" />
            <Format>image/svg</Format>
          </ExternalGraphic><Size>38</Size></Graphic></PointSymbolizer>
          <LineSymbolizer>
            <Stroke><GraphicStroke><Graphic><Mark>
              <WellKnownName>wkt://MULTILINESTRING((-0.5 0,0.2 0),(0.2 -0.15,0.5 0.15),(0.2 0.15,0.5 -0.15),(-0.5 -0.5,-0.5 -0.5),(-0.5 0.5,-0.5 0.5))</WellKnownName>
              <Stroke><CssParameter name="stroke">#FF0000</CssParameter><CssParameter name="stroke-width">1.13</CssParameter><CssParameter name="stroke-linecap">butt</CssParameter><CssParameter name="stroke-linejoin">round</CssParameter></Stroke>
            </Mark><Size>37.8</Size></Graphic></GraphicStroke></Stroke>
            <VendorOption name="graphic-margin">0</VendorOption>
          </LineSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>