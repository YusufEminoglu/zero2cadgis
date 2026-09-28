<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
	<NamedLayer>
		<Name>CDP_ARAZI_KULLANIMI_DEVAM_ETTIRILEREK_KORUNACAK_ALANLAR</Name>
		<UserStyle>
			<Title>CDP_ARAZI_KULLANIMI_DEVAM_ETTIRILEREK_KORUNACAK_ALANLAR</Title>
			<FeatureTypeStyle>
			<Rule>
          <Title>Dogal Ekolojik Korunacak Alan</Title>
          <ogc:Filter>
            <ogc:PropertyIsEqualTo>
              <ogc:PropertyName>AraziKorumaKullanimTip</ogc:PropertyName>
              <ogc:Literal>DogalVeEkolojikAlan</ogc:Literal>
            </ogc:PropertyIsEqualTo>
          </ogc:Filter>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">#D1FF9B</CssParameter>
            </Fill>
            <Stroke>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <ExternalGraphic>
                    <OnlineResource xlink:type="simple" xlink:href="mpyy-eksik-sembol:DogalKarakteriKorunacakAlan.svg" />
                    <Format>image/svg</Format>
                  </ExternalGraphic>
                  <Size>12</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
          </PolygonSymbolizer>
        </Rule>
		  <Rule>
          <Title>EkolojikOnemeSahipAlan</Title>
          <ogc:Filter>
            <ogc:PropertyIsEqualTo>
              <ogc:PropertyName>AraziKorumaKullanimTip</ogc:PropertyName>
              <ogc:Literal>EkolojikOnemeSahipAlan</ogc:Literal>
            </ogc:PropertyIsEqualTo>
          </ogc:Filter>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <ExternalGraphic>
                    <OnlineResource xlink:type="simple" xlink:href="mpyy-eksik-sembol:EkolojikOnemeSahipAlan.svg" />
                    <Format>image/svg</Format>
                  </ExternalGraphic>
                  <Size>12</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <Stroke>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
            <VendorOption name="graphic-margin">30</VendorOption>
          </PolygonSymbolizer>
        </Rule>
			</FeatureTypeStyle>
		</UserStyle>
	</NamedLayer>
</StyledLayerDescriptor>