<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
	<NamedLayer>
		<Name>UIP_KORUMA_KUSAKLARI</Name>
		<UserStyle>
			<Title>UIP_KORUMA_KUSAKLARI</Title>
			<FeatureTypeStyle>
				<Rule>
					<Name>0</Name>
					<Title>NUKLEER_ENERJI_KORUMA_KUSAGI</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>KusakTip</ogc:PropertyName>
							<ogc:Literal>NukleerEnerjiKorumaKusagi</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<CssParameter name="fill">#F57A7A</CssParameter>
							<CssParameter name="fill-opacity">0.5</CssParameter>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://UIP_10_2#0x0054</WellKnownName>
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
										<WellKnownName>ttf://UIP_10_2#0x0055</WellKnownName>
										<Fill>
											<CssParameter name="fill">#FF0000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#FF0000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>10</Size>
								</Graphic>
							</GraphicStroke>
							<CssParameter name="stroke-dasharray">6 2</CssParameter>
						</Stroke>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>HAVAALANI_KORUMA_KUSAGI</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>KusakTip</ogc:PropertyName>
							<ogc:Literal>HavaalaniKorumaKusagi</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<CssParameter name="fill">#F57A7A</CssParameter>
							<CssParameter name="fill-opacity">0.5</CssParameter>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://UIP_10_1#0x0032</WellKnownName>
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
										<WellKnownName>ttf://UIP_10_1#0x0033</WellKnownName>
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
							<CssParameter name="stroke-dasharray">30 2</CssParameter>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>HKK</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">4</CssParameter>
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
						<VendorOption name="repeat">200</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>KARAYOLU_KORUMA_KUSAGI</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>KusakTip</ogc:PropertyName>
							<ogc:Literal>KarayoluKorumaKusagi</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<CssParameter name="fill">#F57A7A</CssParameter>
							<CssParameter name="fill-opacity">0.5</CssParameter>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://UIP_10_2#0x006b</WellKnownName>
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
										<WellKnownName>ttf://UIP_10_1#0x0033</WellKnownName>
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
							<CssParameter name="stroke-dasharray">30 2</CssParameter>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>YKK</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">4</CssParameter>
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
						<VendorOption name="repeat">200</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>BORU_HATTI_KORUMA_KUSAGI</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>KusakTip</ogc:PropertyName>
							<ogc:Literal>BoruHattiKorumaKusagi</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<CssParameter name="fill">#F57A7A</CssParameter>
							<CssParameter name="fill-opacity">0.5</CssParameter>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://UIP_10_1#0x0043</WellKnownName>
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
										<WellKnownName>ttf://UIP_10_1#0x0033</WellKnownName>
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
							<CssParameter name="stroke-dasharray">30 2</CssParameter>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>BHK</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">4</CssParameter>
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
						<VendorOption name="repeat">200</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>SU_KANALI_KORUMA_KUSAGI</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>KusakTip</ogc:PropertyName>
							<ogc:Literal>SuKanaliKorumaKusagi</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<CssParameter name="fill">#F57070</CssParameter>
							<CssParameter name="fill-opacity">0.5</CssParameter>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://UIP_10_3#0x0073</WellKnownName>
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
										<WellKnownName>ttf://UIP_10_1#0x0033</WellKnownName>
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
							<CssParameter name="stroke-dasharray">30 2</CssParameter>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>SKK</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">4</CssParameter>
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
						<VendorOption name="repeat">200</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>ICMESUYU_KORUMA_KUSAGI</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>KusakTip</ogc:PropertyName>
							<ogc:Literal>IcmesuyuKorumaKusagi</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<CssParameter name="fill">#F57070</CssParameter>
							<CssParameter name="fill-opacity">0.5</CssParameter>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://UIP_10_2#0x0063</WellKnownName>
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
										<WellKnownName>ttf://UIP_10_1#0x0033</WellKnownName>
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
							<CssParameter name="stroke-dasharray">30 2</CssParameter>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>ISK</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">4</CssParameter>
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
						<VendorOption name="repeat">200</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>YERALTI_SU_KORUMA_KUSAGI</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>KusakTip</ogc:PropertyName>
							<ogc:Literal>YeraltiSuKorumaKusagi</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<CssParameter name="fill">#F57070</CssParameter>
							<CssParameter name="fill-opacity">0.5</CssParameter>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://UIP_10_3#0x0034</WellKnownName>
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
										<WellKnownName>ttf://UIP_10_1#0x0033</WellKnownName>
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
							<CssParameter name="stroke-dasharray">30 2</CssParameter>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>YSK</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">4</CssParameter>
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
						<VendorOption name="repeat">200</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>DEMIRYOLU_KORUMA_KUSAGI</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>KusakTip</ogc:PropertyName>
							<ogc:Literal>DemiryoluKorumaKusagi</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<CssParameter name="fill">#F57070</CssParameter>
							<CssParameter name="fill-opacity">0.5</CssParameter>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://UIP_10_1#0x0045</WellKnownName>
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
										<WellKnownName>ttf://UIP_10_1#0x0033</WellKnownName>
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
							<CssParameter name="stroke-dasharray">30 2</CssParameter>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>DKK</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">4</CssParameter>
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
						<VendorOption name="repeat">200</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>JEOTERMAL_KORUMA_KUSAGI</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>KusakTip</ogc:PropertyName>
							<ogc:Literal>JeotermalKorumaKusagi</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://UIP_10_2#0x002c</WellKnownName>
										<Fill>
											<CssParameter name="fill">#FF0000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#FF0000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>10</Size>
								</Graphic>
							</GraphicStroke>
							<CssParameter name="stroke-dasharray">10 1</CssParameter>
						</Stroke>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>YANICI_PATLAYICI_MADDE_KORUMA_KUSAGI</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>KusakTip</ogc:PropertyName>
							<ogc:Literal>YaniciPatlayiciMaddeKorumaKusagi</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<CssParameter name="fill">#F57070</CssParameter>
							<CssParameter name="fill-opacity">0.5</CssParameter>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://UIP_10_3#0x0059</WellKnownName>
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
										<WellKnownName>ttf://UIP_10_1#0x0033</WellKnownName>
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
							<CssParameter name="stroke-dasharray">30 2</CssParameter>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>YPK</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">4</CssParameter>
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
						<VendorOption name="repeat">200</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>SAGLIK_KORUMA_BANDI</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>KusakTip</ogc:PropertyName>
							<ogc:Literal>SaglikKorumaBandi</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<CssParameter name="fill">#F57A70</CssParameter>
							<CssParameter name="fill-opacity">0.5</CssParameter>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://UIP_10_3#0x0067</WellKnownName>
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
										<WellKnownName>ttf://UIP_10_1#0x0033</WellKnownName>
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
							<CssParameter name="stroke-dasharray">30 2</CssParameter>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>SKB</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">4</CssParameter>
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
						<VendorOption name="repeat">200</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>ENERJI_NAKIL_HATTI_KORUMA_KUSAGI</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>KusakTip</ogc:PropertyName>
							<ogc:Literal>EnerjiNakilHattiKorumaKusagi</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<CssParameter name="fill">#F57070</CssParameter>
							<CssParameter name="fill-opacity">0.5</CssParameter>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://UIP_10_1#0x002f</WellKnownName>
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
										<WellKnownName>ttf://UIP_10_1#0x0033</WellKnownName>
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
							<CssParameter name="stroke-dasharray">30 2</CssParameter>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>ENH</Label>
						<Font>
							<CssParameter name="font-family">Calibri</CssParameter>
							<CssParameter name="font-size">4</CssParameter>
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
						<VendorOption name="repeat">200</VendorOption>
					</TextSymbolizer>
				</Rule>
			</FeatureTypeStyle>
		</UserStyle>
	</NamedLayer>
</StyledLayerDescriptor>