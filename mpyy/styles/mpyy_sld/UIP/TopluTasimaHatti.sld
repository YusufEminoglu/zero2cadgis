<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
	<NamedLayer>
		<Name>UIP_TOPLU_TASIMA_HATTI</Name>
		<UserStyle>
			<Title>UIP_TOPLU_TASIMA_HATTI</Title>
			<FeatureTypeStyle>
				<Rule>
					<Name>0</Name>
					<Title>RAYLI_TOPLU_TASIMA_YERALTI</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>TopluHatTip</ogc:PropertyName>
							<ogc:Literal>RayliTopluTasimaYerAlti</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://UIP_10_3#0x0061</WellKnownName>
										<Fill>
											<CssParameter name="fill">#000000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#000000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>10</Size>
								</Graphic>
							</GraphicStroke>
						</Stroke>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>RAYLI_TOPLU_TASIMA_YERUSTU</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>TopluHatTip</ogc:PropertyName>
							<ogc:Literal>RayliTopluTasimaYerUstu</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://UIP_10_3#0x0061</WellKnownName>
										<Fill>
											<CssParameter name="fill">#000000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#000000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>10</Size>
								</Graphic>
							</GraphicStroke>
						</Stroke>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>HAVAI_HAT</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>TopluHatTip</ogc:PropertyName>
							<ogc:Literal>HavaiHat</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://UIP_10_1#0x0035</WellKnownName>
										<Fill>
											<CssParameter name="fill">#000000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#000000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>10</Size>
								</Graphic>
							</GraphicStroke>
						</Stroke>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>HAVARAY</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>TopluHatTip</ogc:PropertyName>
							<ogc:Literal>Havaray</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://UIP_10_1#0x0038</WellKnownName>
										<Fill>
											<CssParameter name="fill">#000000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#000000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>10</Size>
								</Graphic>
							</GraphicStroke>
						</Stroke>
					</LineSymbolizer>
				</Rule>
			</FeatureTypeStyle>
		</UserStyle>
	</NamedLayer>
</StyledLayerDescriptor>