<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
	<NamedLayer>
		<Name>UIP_TARIM</Name>
		<UserStyle>
			<Title>UIP_TARIM</Title>
			<FeatureTypeStyle>
				<Rule>
					<Name>0</Name>
					<Title>ZEYTINLIK</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>TarimTip</ogc:PropertyName>
							<ogc:Literal>Zeytinlik</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:0430871f-409a-4d2f-bb02-f8acfcaf01bc.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>ORTU_ALTI_TARIM</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>TarimTip</ogc:PropertyName>
							<ogc:Literal>OrtuAltiTarim</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:864a172f-e2c7-4b52-b07c-75741f143346.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://UIP_10_2#0x005a</WellKnownName>
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
					<Name>0</Name>
					<Title>ORGANIK_TARIM</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>TarimTip</ogc:PropertyName>
							<ogc:Literal>OrganikTarim</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:2c9a19ff-8be4-42eb-9461-379f969ff4d5.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://UIP_10_2#0x0059</WellKnownName>
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
					<Name>0</Name>
					<Title>TARIMSAL_NITELIKLI_ALAN</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>TarimTip</ogc:PropertyName>
							<ogc:Literal>TarımsalNitelikliAlan</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:6e6c2efa-6c73-4b38-aca7-89430ba1f245.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
				</Rule>
			</FeatureTypeStyle>
		</UserStyle>
	</NamedLayer>
</StyledLayerDescriptor>