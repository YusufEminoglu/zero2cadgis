<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
	<NamedLayer>
		<Name>CDP_PLAN_SINIRI</Name>
		<UserStyle>
			<Title>CDP_PLAN_SINIRI</Title>
			<FeatureTypeStyle>
				<Rule>
					<Name>0</Name>
					<Title>PLAN</Title>
					<MaxScaleDenominator>500000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>NitelikTip</ogc:PropertyName>
							<ogc:Literal>Plan</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://UIP_10_3#0x0074</WellKnownName>
										<Fill>
											<CssParameter name="fill">#005CE6</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#005CE6</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>15</Size>
								</Graphic>
							</GraphicStroke>
							<CssParameter name="stroke-dasharray">20 2</CssParameter>
						</Stroke>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>REVIZYON</Title>
					<MaxScaleDenominator>500000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>NitelikTip</ogc:PropertyName>
							<ogc:Literal>Revizyon</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://UIP_10_3#0x0074</WellKnownName>
										<Fill>
											<CssParameter name="fill">#005CE6</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#005CE6</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>15</Size>
								</Graphic>
							</GraphicStroke>
							<CssParameter name="stroke-dasharray">20 2</CssParameter>
						</Stroke>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>ILAVE</Title>
					<MaxScaleDenominator>500000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>NitelikTip</ogc:PropertyName>
							<ogc:Literal>Ilave</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://UIP_10_3#0x0074</WellKnownName>
										<Fill>
											<CssParameter name="fill">#005CE6</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#005CE6</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>15</Size>
								</Graphic>
							</GraphicStroke>
							<CssParameter name="stroke-dasharray">20 2</CssParameter>
						</Stroke>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>ILAVE_REVIZYON</Title>
					<MaxScaleDenominator>500000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>NitelikTip</ogc:PropertyName>
							<ogc:Literal>IlaveRevizyon</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://UIP_10_3#0x0074</WellKnownName>
										<Fill>
											<CssParameter name="fill">#005CE6</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#005CE6</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>15</Size>
								</Graphic>
							</GraphicStroke>
							<CssParameter name="stroke-dasharray">20 2</CssParameter>
						</Stroke>
					</LineSymbolizer>
				</Rule>
			</FeatureTypeStyle>
		</UserStyle>
	</NamedLayer>
</StyledLayerDescriptor>