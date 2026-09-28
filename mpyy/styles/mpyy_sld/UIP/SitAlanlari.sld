<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
	<NamedLayer>
		<Name>UIP_SIT_ALANLARI</Name>
		<UserStyle>
			<Title>UIP_SIT_ALANLARI</Title>
			<FeatureTypeStyle>
				<Rule>
					<Name>0</Name>
					<Title>1_DERECE_ARKEOLOJIK_SIT</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>SitTip</ogc:PropertyName>
							<ogc:Literal>1DereceArkeolojikSit</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:21731b7e-bcd1-43c5-a2c1-6acf081cdc29.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://OG_V_1_1#0x0061</WellKnownName>
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
										<WellKnownName>ttf://OG_V_1_1#0x0062</WellKnownName>
										<Fill>
											<CssParameter name="fill">#FF0000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#FF0000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>30</Size>
								</Graphic>
							</GraphicStroke>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>A1</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">5</CssParameter>
							<CssParameter name="font-style">normal</CssParameter>
						</Font>
						<LabelPlacement>
							<LinePlacement>
								<PerpendicularOffset>
       5
    </PerpendicularOffset>
							</LinePlacement>
						</LabelPlacement>
						<Fill>
							<CssParameter name="fill">#FF0000</CssParameter>
						</Fill>
						<VendorOption name="conflictResolution">false</VendorOption>
						<VendorOption name="repeat">100</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>2_DERECE_ARKEOLOJIK_SIT</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>SitTip</ogc:PropertyName>
							<ogc:Literal>2DereceArkeolojikSit</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:ffd98b3c-efb6-4645-8176-3fe271b52eb2.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://OG_V_1_1#0x0064</WellKnownName>
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
					<LineSymbolizer>
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://OG_V_1_1#0x0065</WellKnownName>
										<Fill>
											<CssParameter name="fill">#FF0000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#FF0000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>30</Size>
								</Graphic>
							</GraphicStroke>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>A2</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">5</CssParameter>
							<CssParameter name="font-style">normal</CssParameter>
						</Font>
						<LabelPlacement>
							<LinePlacement>
								<PerpendicularOffset>
       5
    </PerpendicularOffset>
							</LinePlacement>
						</LabelPlacement>
						<Fill>
							<CssParameter name="fill">#FF0000</CssParameter>
						</Fill>
						<VendorOption name="conflictResolution">false</VendorOption>
						<VendorOption name="repeat">50</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>3_DERECE_ARKEOLOJIK_SIT</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>SitTip</ogc:PropertyName>
							<ogc:Literal>3DereceArkeolojikSit</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:97d7ca4d-f044-45c7-baf4-aa5e7940c456.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://OG_V_1_1#0x0067</WellKnownName>
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
										<WellKnownName>ttf://OG_V_1_1#0x0068</WellKnownName>
										<Fill>
											<CssParameter name="fill">#FF0000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#FF0000</CssParameter>
											<CssParameter name="stroke-width">1</CssParameter>
										</Stroke>
									</Mark>
									<Size>30</Size>
								</Graphic>
							</GraphicStroke>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>A3</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">5</CssParameter>
							<CssParameter name="font-style">normal</CssParameter>
						</Font>
						<LabelPlacement>
							<LinePlacement>
								<PerpendicularOffset>
       5
    </PerpendicularOffset>
							</LinePlacement>
						</LabelPlacement>
						<Fill>
							<CssParameter name="fill">#FF0000</CssParameter>
						</Fill>
						<VendorOption name="conflictResolution">false</VendorOption>
						<VendorOption name="repeat">50</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>KESIN_KORUNACAK_HASSAS_ALAN</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>SitTip</ogc:PropertyName>
							<ogc:Literal>KesinKorunacakHassasAlan</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:d3162c13-e4a2-41cc-a339-58af66abd06e.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://OG_V_1_1#0x0057</WellKnownName>
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
										<WellKnownName>ttf://OG_V_1_1#0x0062</WellKnownName>
										<Fill>
											<CssParameter name="fill">#FF0000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#FF0000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>30</Size>
								</Graphic>
							</GraphicStroke>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>KK</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">5</CssParameter>
							<CssParameter name="font-style">normal</CssParameter>
						</Font>
						<LabelPlacement>
							<LinePlacement>
								<PerpendicularOffset>
       5
    </PerpendicularOffset>
							</LinePlacement>
						</LabelPlacement>
						<Fill>
							<CssParameter name="fill">#FF0000</CssParameter>
						</Fill>
						<VendorOption name="conflictResolution">false</VendorOption>
						<VendorOption name="repeat">50</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>NITELIKLI_DOGAL_KORUMA_ALANI</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>SitTip</ogc:PropertyName>
							<ogc:Literal>NitelikliDogalKorumaAlani</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:bd743b46-ef15-4802-88c4-b33eed9e2be3.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://OG_V_1_2#0x0061</WellKnownName>
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
										<WellKnownName>ttf://OG_V_1_1#0x0065</WellKnownName>
										<Fill>
											<CssParameter name="fill">#FF0000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#FF0000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>30</Size>
								</Graphic>
							</GraphicStroke>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>ND</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">5</CssParameter>
							<CssParameter name="font-style">normal</CssParameter>
						</Font>
						<LabelPlacement>
							<LinePlacement>
								<PerpendicularOffset>
       5
    </PerpendicularOffset>
							</LinePlacement>
						</LabelPlacement>
						<Fill>
							<CssParameter name="fill">#FF0000</CssParameter>
						</Fill>
						<VendorOption name="conflictResolution">false</VendorOption>
						<VendorOption name="repeat">50</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>SURDURULEBILIR_KORUMA_KONTROLLU_KULLANIM_ALANI</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>SitTip</ogc:PropertyName>
							<ogc:Literal>SurdurulebilirKorumaKontrolluKullanimAlani</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:8f32e2af-eaec-439f-9c76-2bfd14cb4235.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://OG_V_1_2#0x0077</WellKnownName>
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
										<WellKnownName>ttf://OG_V_1_1#0x0068</WellKnownName>
										<Fill>
											<CssParameter name="fill">#FF0000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#FF0000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>30</Size>
								</Graphic>
							</GraphicStroke>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>SK</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">5</CssParameter>
							<CssParameter name="font-style">normal</CssParameter>
						</Font>
						<LabelPlacement>
							<LinePlacement>
								<PerpendicularOffset>
       5
    </PerpendicularOffset>
							</LinePlacement>
						</LabelPlacement>
						<Fill>
							<CssParameter name="fill">#FF0000</CssParameter>
						</Fill>
						<VendorOption name="conflictResolution">false</VendorOption>
						<VendorOption name="repeat">50</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>KENTSEL_SIT</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>SitTip</ogc:PropertyName>
							<ogc:Literal>KentselSit</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:e811ed85-fc68-43c5-a34f-a7eacdbdc2f7.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://OG_V_1_1#0x0055</WellKnownName>
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
										<WellKnownName>ttf://OG_V_1_1#0x0062</WellKnownName>
										<Fill>
											<CssParameter name="fill">#FF0000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#FF0000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>30</Size>
								</Graphic>
							</GraphicStroke>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>KS</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">5</CssParameter>
							<CssParameter name="font-style">normal</CssParameter>
						</Font>
						<LabelPlacement>
							<LinePlacement>
								<PerpendicularOffset>
       5
    </PerpendicularOffset>
							</LinePlacement>
						</LabelPlacement>
						<Fill>
							<CssParameter name="fill">#FF0000</CssParameter>
						</Fill>
						<VendorOption name="conflictResolution">false</VendorOption>
						<VendorOption name="repeat">50</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>TARIHI_SIT</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>SitTip</ogc:PropertyName>
							<ogc:Literal>TarihiSit</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:8273bbba-fd7d-4f81-ad7a-a978df17a11c.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://OG_V_1_2#0x0044</WellKnownName>
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
										<WellKnownName>ttf://OG_V_1_1#0x0062</WellKnownName>
										<Fill>
											<CssParameter name="fill">#FF0000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#FF0000</CssParameter>
											<CssParameter name="stroke-width">1</CssParameter>
										</Stroke>
									</Mark>
									<Size>30</Size>
								</Graphic>
							</GraphicStroke>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>TS</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">5</CssParameter>
							<CssParameter name="font-style">normal</CssParameter>
						</Font>
						<LabelPlacement>
							<LinePlacement>
								<PerpendicularOffset>
       5
    </PerpendicularOffset>
							</LinePlacement>
						</LabelPlacement>
						<Fill>
							<CssParameter name="fill">#FF0000</CssParameter>
						</Fill>
						<VendorOption name="conflictResolution">false</VendorOption>
						<VendorOption name="repeat">50</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>SIT_ETKILESIMLI_ALANI</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>SitTip</ogc:PropertyName>
							<ogc:Literal>SitEtkilesimAlani</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://UIP_10_3#0x002c</WellKnownName>
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
										<WellKnownName>ttf://UIP_10_3#0x0035</WellKnownName>
										<Fill>
											<CssParameter name="fill">#FF0000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#FF0000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>30</Size>
								</Graphic>
							</GraphicStroke>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer>
						<Label>SEG</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">5</CssParameter>
							<CssParameter name="font-style">normal</CssParameter>
						</Font>
						<LabelPlacement>
							<LinePlacement>
								<PerpendicularOffset>
       5
    </PerpendicularOffset>
							</LinePlacement>
						</LabelPlacement>
						<Fill>
							<CssParameter name="fill">#FF0000</CssParameter>
						</Fill>
						<VendorOption name="conflictResolution">false</VendorOption>
						<VendorOption name="repeat">50</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>1_DERECE_DOGAL_SIT</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>SitTip</ogc:PropertyName>
							<ogc:Literal>1DereceDogalSit</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:1e69e43a-47fe-40b6-a121-bbcbe88564cd.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://UIP_10_1#0x0061</WellKnownName>
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
										<WellKnownName>ttf://UIP_10_1#0x0062</WellKnownName>
										<Fill>
											<CssParameter name="fill">#FF0000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#FF0000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>20</Size>
								</Graphic>
							</GraphicStroke>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>D1</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">5</CssParameter>
							<CssParameter name="font-style">normal</CssParameter>
						</Font>
						<LabelPlacement>
							<LinePlacement>
								<PerpendicularOffset>
       5
    </PerpendicularOffset>
							</LinePlacement>
						</LabelPlacement>
						<Fill>
							<CssParameter name="fill">#FF0000</CssParameter>
						</Fill>
						<VendorOption name="conflictResolution">false</VendorOption>
						<VendorOption name="repeat">50</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>2_DERECE_DOGAL_SIT</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>SitTip</ogc:PropertyName>
							<ogc:Literal>2DereceDogalSit</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:a5af854d-3ebc-4260-9eb4-0fb55360f75e.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://UIP_10_1#0x0030</WellKnownName>
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
										<WellKnownName>ttf://UIP_10_1#0x0064</WellKnownName>
										<Fill>
											<CssParameter name="fill">#FF0000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#FF0000</CssParameter>
											<CssParameter name="stroke-width">1</CssParameter>
										</Stroke>
									</Mark>
									<Size>20</Size>
								</Graphic>
							</GraphicStroke>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>D2</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">5</CssParameter>
							<CssParameter name="font-style">normal</CssParameter>
						</Font>
						<LabelPlacement>
							<LinePlacement>
								<PerpendicularOffset>
       5
    </PerpendicularOffset>
							</LinePlacement>
						</LabelPlacement>
						<Fill>
							<CssParameter name="fill">#FF0000</CssParameter>
						</Fill>
						<VendorOption name="conflictResolution">false</VendorOption>
						<VendorOption name="repeat">50</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>3_DERECE_DOGAL_SIT</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>SitTip</ogc:PropertyName>
							<ogc:Literal>3DereceDogalSit</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:28a9507f-97c1-48e2-82a0-7a73dcb5e9b6.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://UIP_10_1#0x0066</WellKnownName>
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
										<WellKnownName>ttf://UIP_10_1#0x0067</WellKnownName>
										<Fill>
											<CssParameter name="fill">#FF0000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#FF0000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>20</Size>
								</Graphic>
							</GraphicStroke>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>D3</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">5</CssParameter>
							<CssParameter name="font-style">normal</CssParameter>
						</Font>
						<LabelPlacement>
							<LinePlacement>
								<PerpendicularOffset>
       5
    </PerpendicularOffset>
							</LinePlacement>
						</LabelPlacement>
						<Fill>
							<CssParameter name="fill">#FF0000</CssParameter>
						</Fill>
						<VendorOption name="conflictResolution">false</VendorOption>
						<VendorOption name="repeat">50</VendorOption>
					</TextSymbolizer>
				</Rule>
		<Rule>
          <Title>KENTSEL_ARKEOLOJIK_SIT</Title>
          <ogc:Filter>
            <ogc:PropertyIsEqualTo>
              <ogc:PropertyName>SitTip</ogc:PropertyName>
              <ogc:Literal>KentselArkeolojikSit</ogc:Literal>
            </ogc:PropertyIsEqualTo>
          </ogc:Filter>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>wkt://MULTILINESTRING((0.00 1.09,1.00 1.09),(0.00 -0.09,1.00 -0.09))</WellKnownName>
                    <Fill />
                    <Stroke />
                  </Mark>
                </Graphic>
              </GraphicFill>
            </Fill>
            <Stroke>
              <CssParameter name="stroke">#ff0000</CssParameter>
              <CssParameter name="stroke-dasharray">0.0</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Stroke>
              <GraphicStroke>
                <Graphic>
                  <Mark>
                    <WellKnownName>circle</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#ff0000</CssParameter>
                    </Fill>
                  </Mark>
                  <Size>11</Size>
                </Graphic>
              </GraphicStroke>
              <CssParameter name="stroke-dashoffset">0</CssParameter>
              <CssParameter name="stroke-dasharray">11.0 73.0</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Stroke>
              <GraphicStroke>
                <Graphic>
                  <Mark>
                    <WellKnownName>wkt://MULTILINESTRING((0 0,0 1),(0 0.5,0.42 1),(0 0.5,0.42 0),(0.55 0,0.78 1,1 0),(0.64 0.45,0.89 0.45))</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#ff0000</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>14</Size>
                </Graphic>
              </GraphicStroke>
              <CssParameter name="stroke-dashoffset">50</CssParameter>
              <CssParameter name="stroke-dasharray">14.0 70.0</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource xlink:type="simple" xlink:href="mpyy-eksik-sembol:KentselArkeolojikSitAlani.svg" />
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