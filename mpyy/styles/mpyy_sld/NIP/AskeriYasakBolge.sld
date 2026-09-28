<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>NIP_ASKERI_YASAK_BOLGE</Name>
    <UserStyle>
      <Title>NIP_ASKERI_YASAK_BOLGE</Title>
      <FeatureTypeStyle>
        <Rule>
          <Name>0</Name>
          <Title>NIP_ASKERI_YASAK_BOLGE</Title>
          <MaxScaleDenominator>80000</MaxScaleDenominator>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <ExternalGraphic>
                    <OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:c040de15-e463-4079-b8e9-b8ea9294aea2.png" />
                    <Format>image/png</Format>
                  </ExternalGraphic>
                </Graphic>
              </GraphicFill>
            </Fill>
          </PolygonSymbolizer>
          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource xlink:type="simple" xlink:href="mpyy-eksik-sembol:AskeriAlan.svg" />
                <Format>image/svg</Format>
              </ExternalGraphic>
              <Size>38</Size>
            </Graphic>
          </PointSymbolizer>
          <LineSymbolizer>
            <Stroke>
              <GraphicStroke>
                <Graphic>
                  <Mark>
                    <WellKnownName>wkt://MULTILINESTRING((-0.5 0,0.2 0),(0.2 -0.15,0.5 0.15),(0.2 0.15,0.5 -0.15),(-0.5 -0.5,-0.5 -0.5),(-0.5 0.5,-0.5 0.5))</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#FF0000</CssParameter>
                      <CssParameter name="stroke-width">1.13</CssParameter>
                      <CssParameter name="stroke-linecap">butt</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>37.8</Size>
                </Graphic>
              </GraphicStroke>
            </Stroke>
            <VendorOption name="graphic-margin">0</VendorOption>
          </LineSymbolizer>
          <LineSymbolizer>
            <Stroke>
              <GraphicStroke>
                <Graphic>
                  <Mark>
                    <WellKnownName>wkt://MULTILINESTRING((0 0,0.14 1,0.28 0),(0.06 0.42,0.22 0.42),(0.36 1,0.50 0.55,0.64 1),(0.50 0.55,0.50 0),(0.72 0,0.72 1),(0.72 1,0.92 1,1 0.82,0.92 0.58,0.72 0.58),(0.72 0.58,0.92 0.58,1 0.30,0.92 0,0.72 0))</WellKnownName>
                    <Stroke><CssParameter name="stroke">#FF0000</CssParameter><CssParameter name="stroke-width">1</CssParameter></Stroke>
                  </Mark>
                  <Size>14</Size>
                </Graphic>
              </GraphicStroke>
              <CssParameter name="stroke-dashoffset">0</CssParameter>
              <CssParameter name="stroke-dasharray">14 23.8</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>