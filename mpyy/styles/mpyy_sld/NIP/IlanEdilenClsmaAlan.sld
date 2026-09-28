<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
	<NamedLayer>
		<Name>NIP_ILAN_EDILEN_CLSMA_ALAN</Name>
		<UserStyle>
			<Title>NIP_ILAN_EDILEN_CLSMA_ALAN</Title>
			<FeatureTypeStyle>
				<Rule>
					<Name>0</Name>
					<Title>TEKNOLOJI_GELISTIRME_BOLGESI</Title>
					<MaxScaleDenominator>80000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>IlanEdilenCalismaTip</ogc:PropertyName>
							<ogc:Literal>TeknolojiGelistirmeBolgesi</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:ba149a02-1d44-486a-853c-bf82a29bca41.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://OG_V_1_2#0x0047</WellKnownName>
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
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://OG_V_1_2#0x0048</WellKnownName>
										<Fill>
											<CssParameter name="fill">#000000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#000000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>60</Size>
								</Graphic>
							</GraphicStroke>
							<CssParameter name="stroke-dasharray">60 5</CssParameter>
						</Stroke>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>SERBEST_BOLGE</Title>
					<MaxScaleDenominator>80000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>IlanEdilenCalismaTip</ogc:PropertyName>
							<ogc:Literal>SerbestBolge</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:c0dd5635-39b2-47b6-9187-49025de212a0.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://OG_V_1_2#0x0072</WellKnownName>
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
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://OG_V_1_1#0x0030</WellKnownName>
										<Fill>
											<CssParameter name="fill">#000000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#000000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>60</Size>
								</Graphic>
							</GraphicStroke>
							<CssParameter name="stroke-dasharray">60 5</CssParameter>
						</Stroke>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>OSB</Title>
					<MaxScaleDenominator>80000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>IlanEdilenCalismaTip</ogc:PropertyName>
							<ogc:Literal>Osb</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:22104a42-e8d0-4f05-bbf6-c343019076f3.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://OG_V_1_2#0x006b</WellKnownName>
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
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://OG_V_1_2#0x0056</WellKnownName>
										<Fill>
											<CssParameter name="fill">#000000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#000000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>60</Size>
								</Graphic>
							</GraphicStroke>
							<CssParameter name="stroke-dasharray">60 5</CssParameter>
						</Stroke>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>ENDUSTRI_BOLGESI</Title>
					<MaxScaleDenominator>80000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>IlanEdilenCalismaTip</ogc:PropertyName>
							<ogc:Literal>EndustriBolgesi</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:6b5b43d3-78a5-400d-8f36-b9c45f8a0c8a.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://OG_V_1_1#0x0042</WellKnownName>
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
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://OG_V_1_1#0x0043</WellKnownName>
										<Fill>
											<CssParameter name="fill">#000000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#000000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>60</Size>
								</Graphic>
							</GraphicStroke>
							<CssParameter name="stroke-dasharray">60 5</CssParameter>
						</Stroke>
					</LineSymbolizer>
				</Rule>
			</FeatureTypeStyle>
		</UserStyle>
	</NamedLayer>
</StyledLayerDescriptor>