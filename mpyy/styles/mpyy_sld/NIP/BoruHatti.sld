<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
	<NamedLayer>
		<Name>NIP_BORU_HATTI</Name>
		<UserStyle>
			<Title>NIP_BORU_HATTI</Title>
			<FeatureTypeStyle>
				<Rule>
					<Name>0</Name>
					<Title>PETROL_BORU_HATTI</Title>
					<MaxScaleDenominator>80000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>EnerjiHatTip</ogc:PropertyName>
							<ogc:Literal>PetrolBoruHatti</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://OG_V_1_1#0x0077</WellKnownName>
										<Fill>
											<CssParameter name="fill">#000000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#000000</CssParameter>
											<CssParameter name="stroke-width">0.4</CssParameter>
										</Stroke>
									</Mark>
									<Size>15</Size>
								</Graphic>
							</GraphicStroke>
						</Stroke>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>DOGALGAZ_BORU_HATTI</Title>
					<MaxScaleDenominator>80000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>EnerjiHatTip</ogc:PropertyName>
							<ogc:Literal>DogalgazBoruHatti</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://OG_V_1_1#0x0077</WellKnownName>
										<Fill>
											<CssParameter name="fill">#000000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#000000</CssParameter>
											<CssParameter name="stroke-width">0.4</CssParameter>
										</Stroke>
									</Mark>
									<Size>15</Size>
								</Graphic>
							</GraphicStroke>
						</Stroke>
					</LineSymbolizer>
				</Rule>
			</FeatureTypeStyle>
		</UserStyle>
	</NamedLayer>
</StyledLayerDescriptor>