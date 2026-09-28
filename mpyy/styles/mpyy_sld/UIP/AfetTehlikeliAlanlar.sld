<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
	<NamedLayer>
		<Name>UIP_AFET_TEHLIKELI_ALANLAR</Name>
		<UserStyle>
			<Title>UIP_AFET_TEHLIKELI_ALANLAR</Title>
			<FeatureTypeStyle>
				<Rule>
					<Name>0</Name>
					<Title>YAPI_YASAKLI_ALAN</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>AfetTip</ogc:PropertyName>
							<ogc:Literal>YapiYasakliAlan</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:1762a074-9bcc-4e2b-bd24-579d7fdcb653.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://nazim_imar_00#0x004d</WellKnownName>
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
							<CssParameter name="stroke">#000000</CssParameter>
							<CssParameter name="stroke-width">0.3528</CssParameter>
							<CssParameter name="stroke-dasharray">2 2</CssParameter>
						</Stroke>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>HEYELAN_ALANI</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>AfetTip</ogc:PropertyName>
							<ogc:Literal>HeyelanAlani</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:32c0328d-8050-4402-bb5e-1d80b2621969.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://UIP_10_1#0x002c</WellKnownName>
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
										<WellKnownName>ttf://UIP_10_3#0x0079</WellKnownName>
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
						</Stroke>
					</LineSymbolizer>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://UIP_10_3#0x0079</WellKnownName>
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
						</Stroke>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>TASKINA_MARUZ_ALAN</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>AfetTip</ogc:PropertyName>
							<ogc:Literal>TaskinaMaruzAlan</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:3e1d9528-0db1-4b19-96a0-d034d810fae9.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
							<CssParameter name="fill-opacity">0.5</CssParameter>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Graphic>
							<Mark>
								<WellKnownName>ttf://UIP_10_3#0x0076</WellKnownName>
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
										<WellKnownName>ttf://DejaVu Sans#0x0056</WellKnownName>
										<Fill>
											<CssParameter name="fill">#FF0000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#FF0000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
											<CssParameter name="stroke-dasharray">4 1 4 1 4 8</CssParameter>
										</Stroke>
									</Mark>
									<Size>4</Size>
									<Displacement>
										<DisplacementX>0</DisplacementX>
										<DisplacementY>2</DisplacementY>
									</Displacement>
                                  	<Rotation>180</Rotation>
								</Graphic>
							</GraphicStroke>
						</Stroke>
					</LineSymbolizer>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://DejaVu Sans#0x005f</WellKnownName>
										<Fill>
											<CssParameter name="fill">#FF0000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke-opacity">0</CssParameter>
											<CssParameter name="stroke">#FF0000</CssParameter>
											<CssParameter name="stroke-width">0.3</CssParameter>
										</Stroke>
									</Mark>
									<Size>4</Size>
									<Displacement>
										<DisplacementX>0</DisplacementX>
										<DisplacementY>0</DisplacementY>
									</Displacement>
                                  	<Rotation>180</Rotation>
								</Graphic>
							</GraphicStroke>
						</Stroke>
					</LineSymbolizer>
				</Rule>
								<Rule>
					<Name>0</Name>
					<Title>KENTSEL_RISK_ALANI</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>AfetTip</ogc:PropertyName>
							<ogc:Literal>KentselRiskAlani</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<CssParameter name="fill">transparent</CssParameter>
						</Fill>
						<Stroke>
							<CssParameter name="stroke-width">1.5</CssParameter>
							<CssParameter name="stroke-dasharray">8.0</CssParameter>
						</Stroke>
					</PolygonSymbolizer>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<Mark>
										<WellKnownName>wkt://MULTILINESTRING((0.06 -0.06,1.06 0.94),(0.00 0.00,1.00 1.00),(-0.06 0.06,0.94 1.06))</WellKnownName>
										<Stroke />
									</Mark>
									<Size>40m</Size>
								</Graphic>
							</GraphicFill>
						</Fill>
						<Stroke>
							<CssParameter name="stroke-width">1.5</CssParameter>
							<CssParameter name="stroke-dasharray">8.0</CssParameter>
						</Stroke>
					</PolygonSymbolizer>
					<PointSymbolizer>
						<Graphic>
							<ExternalGraphic>
								<OnlineResource xlink:type="simple" xlink:href="mpyy-eksik-sembol:KentselRiskAlani.svg" />
								<Format>image/svg</Format>
							</ExternalGraphic>
							<Size>40m</Size>
						</Graphic>
					</PointSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>TSUNAMI_RISKLI_ALAN</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>AfetTip</ogc:PropertyName>
							<ogc:Literal>TsunamiRiskliAlan</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<CssParameter name="fill">#E1E1E1</CssParameter>
						</Fill>
						<Stroke>
							<CssParameter name="stroke">#ff0000</CssParameter>
							<CssParameter name="stroke-linecap">square</CssParameter>
							<CssParameter name="stroke-linejoin">bevel</CssParameter>
							<CssParameter name="stroke-dasharray">0.0</CssParameter>
						</Stroke>
					</PolygonSymbolizer>
					<PolygonSymbolizer>
						<Fill>
							<CssParameter name="fill">#E1E1E1</CssParameter>
						</Fill>
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://Tahoma#0x02c4</WellKnownName>
										<Fill>
											<CssParameter name="fill">#ff0000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke">#ff0000</CssParameter>
										</Stroke>
									</Mark>
									<Size>11</Size>
									<Displacement>
										<DisplacementX>5</DisplacementX>
										<DisplacementY>5</DisplacementY>
									</Displacement>
								</Graphic>
							</GraphicStroke>
							<CssParameter name="stroke-dashoffset">13.25</CssParameter>
							<CssParameter name="stroke-dasharray">11.0 57.0</CssParameter>
						</Stroke>
					</PolygonSymbolizer>
					<PolygonSymbolizer>
						<Fill>
							<CssParameter name="fill">#E1E1E1</CssParameter>
						</Fill>
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://Tahoma#0x02c4</WellKnownName>
										<Fill>
											<CssParameter name="fill">#ff0000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke">#ff0000</CssParameter>
										</Stroke>
									</Mark>
									<Size>11</Size>
									<Displacement>
										<DisplacementX>5</DisplacementX>
										<DisplacementY>5</DisplacementY>
									</Displacement>
								</Graphic>
							</GraphicStroke>
							<CssParameter name="stroke-dashoffset">26.5</CssParameter>
							<CssParameter name="stroke-dasharray">11.0 57.0</CssParameter>
						</Stroke>
					</PolygonSymbolizer>
					<PolygonSymbolizer>
						<Fill>
							<CssParameter name="fill">#E1E1E1</CssParameter>
						</Fill>
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>ttf://Tahoma#0x02c4</WellKnownName>
										<Fill>
											<CssParameter name="fill">#ff0000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke">#ff0000</CssParameter>
										</Stroke>
									</Mark>
									<Size>11</Size>
									<Displacement>
										<DisplacementX>5</DisplacementX>
										<DisplacementY>5</DisplacementY>
									</Displacement>
								</Graphic>
							</GraphicStroke>
							<CssParameter name="stroke-dashoffset">39.75</CssParameter>
							<CssParameter name="stroke-dasharray">11.0 57.0</CssParameter>
						</Stroke>
					</PolygonSymbolizer>
					<PointSymbolizer>
						<Graphic>
							<ExternalGraphic>
								<OnlineResource xlink:type="simple" xlink:href="mpyy-eksik-sembol:TsunamiRiskliAlan.svg" />
								<Format>image/svg</Format>
							</ExternalGraphic>
							<Size>40m</Size>
						</Graphic>
					</PointSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>KUTLE_HAREKETI_RISKLI_ALAN</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>AfetTip</ogc:PropertyName>
							<ogc:Literal>KutleHareketiRiskliAlan</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">#F57A7A</CssParameter>
            </Fill>
            <Stroke>
              <CssParameter name="stroke">#ff0000</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
              <CssParameter name="stroke-dasharray">0.0</CssParameter>
            </Stroke>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">#F57A7A</CssParameter>
            </Fill>
            <Stroke>
              <GraphicStroke>
                <Graphic>
                  <Mark>
                    <WellKnownName>ttf://Tahoma#0x02c4</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#ff0000</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#ff0000</CssParameter>
                      <CssParameter name="stroke-dasharray">8.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>11</Size>
                  <Displacement>
                    <DisplacementX>5</DisplacementX>
                    <DisplacementY>5</DisplacementY>
                  </Displacement>
                </Graphic>
              </GraphicStroke>
              <CssParameter name="stroke-dashoffset">13.25</CssParameter>
              <CssParameter name="stroke-dasharray">11.0 57.0</CssParameter>
            </Stroke>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">#F57A7A</CssParameter>
            </Fill>
            <Stroke>
              <GraphicStroke>
                <Graphic>
                  <Mark>
                    <WellKnownName>ttf://Tahoma#0x02c4</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#ff0000</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#ff0000</CssParameter>
                      <CssParameter name="stroke-dasharray">8.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>11</Size>
                  <Displacement>
                    <DisplacementX>5</DisplacementX>
                    <DisplacementY>5</DisplacementY>
                  </Displacement>
                </Graphic>
              </GraphicStroke>
              <CssParameter name="stroke-dashoffset">26.5</CssParameter>
              <CssParameter name="stroke-dasharray">11.0 57.0</CssParameter>
            </Stroke>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">#F57A7A</CssParameter>
            </Fill>
            <Stroke>
              <GraphicStroke>
                <Graphic>
                  <Mark>
                    <WellKnownName>ttf://Tahoma#0x02c4</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#ff0000</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#ff0000</CssParameter>
                      <CssParameter name="stroke-dasharray">8.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>11</Size>
                  <Displacement>
                    <DisplacementX>5</DisplacementX>
                    <DisplacementY>5</DisplacementY>
                  </Displacement>
                </Graphic>
              </GraphicStroke>
              <CssParameter name="stroke-dashoffset">39.75</CssParameter>
              <CssParameter name="stroke-dasharray">11.0 57.0</CssParameter>
            </Stroke>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource xlink:type="simple" xlink:href="mpyy-eksik-sembol:KutleHareketiRiskAlan.svg" />
                <Format>image/svg</Format>
              </ExternalGraphic>
              <Size>40m</Size>
            </Graphic>
          </PointSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>FAY_SAKINIM_ZONU_ALANI</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>AfetTip</ogc:PropertyName>
							<ogc:Literal>FaySakinimZonuAlani</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
<PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>wkt://MULTILINESTRING((0.06 -0.06,1.06 0.94),(0.00 0.00,1.00 1.00),(-0.06 0.06,0.94 1.06))</WellKnownName>
                    <Stroke />
                  </Mark>
                  <Size>80</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <Stroke>
              <CssParameter name="stroke">#ff0000</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
              <CssParameter name="stroke-dasharray">0.0</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>wkt://MULTILINESTRING((0.06 -0.06,1.06 0.94),(0.00 0.00,1.00 1.00),(-0.06 0.06,0.94 1.06))</WellKnownName>
                    <Stroke />
                  </Mark>
                  <Size>80</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <Stroke>
              <GraphicStroke>
                <Graphic>
                  <Mark>
                    <WellKnownName>ttf://Tahoma#0x02c4</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#ff0000</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#ff0000</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>11</Size>
                  <Displacement>
                    <DisplacementX>5</DisplacementX>
                    <DisplacementY>5</DisplacementY>
                  </Displacement>
                </Graphic>
              </GraphicStroke>
              <CssParameter name="stroke-dashoffset">13.25</CssParameter>
              <CssParameter name="stroke-dasharray">11.0 57.0</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>wkt://MULTILINESTRING((0.06 -0.06,1.06 0.94),(0.00 0.00,1.00 1.00),(-0.06 0.06,0.94 1.06))</WellKnownName>
                    <Stroke />
                  </Mark>
                  <Size>80</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <Stroke>
              <GraphicStroke>
                <Graphic>
                  <Mark>
                    <WellKnownName>ttf://Tahoma#0x02c4</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#ff0000</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#ff0000</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>11</Size>
                  <Displacement>
                    <DisplacementX>5</DisplacementX>
                    <DisplacementY>5</DisplacementY>
                  </Displacement>
                </Graphic>
              </GraphicStroke>
              <CssParameter name="stroke-dashoffset">26.5</CssParameter>
              <CssParameter name="stroke-dasharray">11.0 57.0</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>wkt://MULTILINESTRING((0.06 -0.06,1.06 0.94),(0.00 0.00,1.00 1.00),(-0.06 0.06,0.94 1.06))</WellKnownName>
                    <Stroke />
                  </Mark>
                  <Size>80</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <Stroke>
              <GraphicStroke>
                <Graphic>
                  <Mark>
                    <WellKnownName>ttf://Tahoma#0x02c4</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#ff0000</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#ff0000</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>11</Size>
                  <Displacement>
                    <DisplacementX>5</DisplacementX>
                    <DisplacementY>5</DisplacementY>
                  </Displacement>
                </Graphic>
              </GraphicStroke>
              <CssParameter name="stroke-dashoffset">39.75</CssParameter>
              <CssParameter name="stroke-dasharray">11.0 57.0</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
				</Rule>
				<VendorOption name="ruleEvaluation">first</VendorOption>
			</FeatureTypeStyle>
						<FeatureTypeStyle>
				<Rule>
					<Name>0</Name>
					<Title>TSUNAMI_RISKLI_ALAN</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>AfetTip</ogc:PropertyName>
							<ogc:Literal>TsunamiRiskliAlan</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>wkt://MULTILINESTRING((0.00 1.00,1.00 0.00))</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke-width">2</CssParameter>
                      <CssParameter name="stroke-dasharray">5.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>25</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <Stroke>
              <CssParameter name="stroke">#ff0000</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
              <CssParameter name="stroke-dasharray">0.0</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>wkt://MULTILINESTRING((0.00 1.00,1.00 0.00))</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke-width">2</CssParameter>
                      <CssParameter name="stroke-dasharray">5.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>25</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <Stroke>
              <GraphicStroke>
                <Graphic>
                  <Mark>
                    <WellKnownName>ttf://Tahoma#0x02c4</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#ff0000</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#ff0000</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>11</Size>
                  <Displacement>
                    <DisplacementX>5</DisplacementX>
                    <DisplacementY>5</DisplacementY>
                  </Displacement>
                </Graphic>
              </GraphicStroke>
              <CssParameter name="stroke-dashoffset">13.25</CssParameter>
              <CssParameter name="stroke-dasharray">11.0 57.0</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>wkt://MULTILINESTRING((0.00 1.00,1.00 0.00))</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke-width">2</CssParameter>
                      <CssParameter name="stroke-dasharray">5.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>25</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <Stroke>
              <GraphicStroke>
                <Graphic>
                  <Mark>
                    <WellKnownName>ttf://Tahoma#0x02c4</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#ff0000</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#ff0000</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>11</Size>
                  <Displacement>
                    <DisplacementX>5</DisplacementX>
                    <DisplacementY>5</DisplacementY>
                  </Displacement>
                </Graphic>
              </GraphicStroke>
              <CssParameter name="stroke-dashoffset">26.5</CssParameter>
              <CssParameter name="stroke-dasharray">11.0 57.0</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>wkt://MULTILINESTRING((0.00 1.00,1.00 0.00))</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke-width">2</CssParameter>
                      <CssParameter name="stroke-dasharray">5.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>25</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <Stroke>
              <GraphicStroke>
                <Graphic>
                  <Mark>
                    <WellKnownName>ttf://Tahoma#0x02c4</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#ff0000</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#ff0000</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>11</Size>
                  <Displacement>
                    <DisplacementX>5</DisplacementX>
                    <DisplacementY>5</DisplacementY>
                  </Displacement>
                </Graphic>
              </GraphicStroke>
              <CssParameter name="stroke-dashoffset">39.75</CssParameter>
              <CssParameter name="stroke-dasharray">11.0 57.0</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource xlink:type="simple" xlink:href="mpyy-eksik-sembol:TsunamiRiskliAlan.svg" />
                <Format>image/svg</Format>
              </ExternalGraphic>
              <Size>40m</Size>
            </Graphic>
          </PointSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>KUTLE_HAREKETI_RISKLI_ALAN</Title>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>AfetTip</ogc:PropertyName>
							<ogc:Literal>KutleHareketiRiskliAlan</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
<PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://horline</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke-width">2</CssParameter>
                      <CssParameter name="stroke-dasharray">8.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>40m</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <Stroke>
              <CssParameter name="stroke">#ff0000</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
              <CssParameter name="stroke-dasharray">0.0</CssParameter>
            </Stroke>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://horline</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke-width">2</CssParameter>
                      <CssParameter name="stroke-dasharray">8.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>40m</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <Stroke>
              <GraphicStroke>
                <Graphic>
                  <Mark>
                    <WellKnownName>ttf://Tahoma#0x02c4</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#ff0000</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#ff0000</CssParameter>
                      <CssParameter name="stroke-dasharray">8.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>11</Size>
                  <Displacement>
                    <DisplacementX>5</DisplacementX>
                    <DisplacementY>5</DisplacementY>
                  </Displacement>
                </Graphic>
              </GraphicStroke>
              <CssParameter name="stroke-dashoffset">13.25</CssParameter>
              <CssParameter name="stroke-dasharray">11.0 57.0</CssParameter>
            </Stroke>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://horline</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke-width">2</CssParameter>
                      <CssParameter name="stroke-dasharray">8.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>40m</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <Stroke>
              <GraphicStroke>
                <Graphic>
                  <Mark>
                    <WellKnownName>ttf://Tahoma#0x02c4</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#ff0000</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#ff0000</CssParameter>
                      <CssParameter name="stroke-dasharray">8.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>11</Size>
                  <Displacement>
                    <DisplacementX>5</DisplacementX>
                    <DisplacementY>5</DisplacementY>
                  </Displacement>
                </Graphic>
              </GraphicStroke>
              <CssParameter name="stroke-dashoffset">26.5</CssParameter>
              <CssParameter name="stroke-dasharray">11.0 57.0</CssParameter>
            </Stroke>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://horline</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke-width">2</CssParameter>
                      <CssParameter name="stroke-dasharray">8.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>40m</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <Stroke>
              <GraphicStroke>
                <Graphic>
                  <Mark>
                    <WellKnownName>ttf://Tahoma#0x02c4</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#ff0000</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#ff0000</CssParameter>
                      <CssParameter name="stroke-dasharray">8.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>11</Size>
                  <Displacement>
                    <DisplacementX>5</DisplacementX>
                    <DisplacementY>5</DisplacementY>
                  </Displacement>
                </Graphic>
              </GraphicStroke>
              <CssParameter name="stroke-dashoffset">39.75</CssParameter>
              <CssParameter name="stroke-dasharray">11.0 57.0</CssParameter>
            </Stroke>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource xlink:type="simple" xlink:href="mpyy-eksik-sembol:KutleHareketiRiskAlan.svg" />
                <Format>image/svg</Format>
              </ExternalGraphic>
              <Size>40m</Size>
            </Graphic>
          </PointSymbolizer>
				</Rule>
				<VendorOption name="ruleEvaluation">first</VendorOption>
			</FeatureTypeStyle>
		</UserStyle>
	</NamedLayer>
</StyledLayerDescriptor>