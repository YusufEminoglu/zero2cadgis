<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
	<NamedLayer>
		<Name>CDP_YERLESIM_ALANI</Name>
		<UserStyle>
			<Title>CDP_YERLESIM_ALANI</Title>
			<FeatureTypeStyle>
				<Rule>
					<Title>BAGLIK BAHCELIK</Title>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>YerlesimTip</ogc:PropertyName>
							<ogc:Literal>BaglikBahcelik</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<CssParameter name="fill">#c8eb00</CssParameter>
						</Fill>
						<Stroke>
							<CssParameter name="stroke-linejoin">bevel</CssParameter>
						</Stroke>
					</PolygonSymbolizer>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<Mark>
										<WellKnownName>shape://horline</WellKnownName>
										<Stroke />
									</Mark>
									<Size>19</Size>
								</Graphic>
							</GraphicFill>
						</Fill>
						<Stroke>
							<CssParameter name="stroke-linejoin">bevel</CssParameter>
						</Stroke>
					</PolygonSymbolizer>
				</Rule>
			</FeatureTypeStyle>
		</UserStyle>
	</NamedLayer>
</StyledLayerDescriptor>