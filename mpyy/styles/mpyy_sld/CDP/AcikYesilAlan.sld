<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
	<NamedLayer>
		<Name>CDP_ACIK_YESIL_ALAN</Name>
		<UserStyle>
			<Title>CDP_ACIK_YESIL_ALAN</Title>
			<FeatureTypeStyle>
				<Rule>
					<Name>0</Name>
					<Title>KENTSEL_BOLGESEL_YESIL_SPOR_ALANI</Title>
					<MaxScaleDenominator>1000000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>AcikYesilTip</ogc:PropertyName>
							<ogc:Literal>KentselBolgeselYesilSporAlani</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:ec1b7f56-4515-4bc7-ba7f-8d42484d2fd7.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>MILLET_BAHCESI</Title>
					<MaxScaleDenominator>500000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>AcikYesilTip</ogc:PropertyName>
							<ogc:Literal>MilletBahcesi</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:a8449595-b945-40eb-b5da-35fb62d29de0.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://Intelli Eplan Extra#0x0041</WellKnownName>
								<Fill>
									<CssParameter name="fill">#000000</CssParameter>
								</Fill>
								<Stroke>
									<CssParameter name="stroke-opacity">0</CssParameter>
									<CssParameter name="stroke">#000000</CssParameter>
									<CssParameter name="stroke-width">1</CssParameter>
								</Stroke>
							</Mark>
							<Size>15</Size>
						</Graphic>
					</PointSymbolizer>
				</Rule>
			<Rule>
          <Title>FuarPanayirFestival</Title>
          <ogc:Filter>
            <ogc:PropertyIsEqualTo>
              <ogc:PropertyName>AcikYesilTip</ogc:PropertyName>
              <ogc:Literal>FuarPanayirFestivalAlani</ogc:Literal>
            </ogc:PropertyIsEqualTo>
          </ogc:Filter>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">#249c22</CssParameter>
            </Fill>
            <Stroke />
            <VendorOption name="random">free</VendorOption>
            <VendorOption name="random-symbol-count">100</VendorOption>
          </PolygonSymbolizer>
          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource xlink:type="simple" xlink:href="mpyy-eksik-sembol:FuarPanayirFestival.svg" />
                <Format>image/svg</Format>
              </ExternalGraphic>
              <Size>38</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
		<Rule>
          <Title>AGACLANDIRILACAK_ALAN</Title>
          <ogc:Filter>
            <ogc:PropertyIsEqualTo>
              <ogc:PropertyName>AcikYesilTip</ogc:PropertyName>
              <ogc:Literal>AgaclandirilacakAlan</ogc:Literal>
            </ogc:PropertyIsEqualTo>
          </ogc:Filter>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">#62ba52</CssParameter>
            </Fill>
            <Stroke>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
            <VendorOption name="graphic-margin">-1 -1 26 26</VendorOption>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>triangle</WellKnownName>
                    <Stroke />
                  </Mark>
                  <Size>11</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <Stroke>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
            <VendorOption name="graphic-margin">-1 -1 26 26</VendorOption>
          </PolygonSymbolizer>
          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource xlink:type="simple" xlink:href="mpyy-eksik-sembol:AgaclandirilacakAlan.svg" />
                <Format>image/svg</Format>
              </ExternalGraphic>
              <Size>38</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
			</FeatureTypeStyle>
		</UserStyle>
	</NamedLayer>
</StyledLayerDescriptor>