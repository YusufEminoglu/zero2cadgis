<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
	<NamedLayer>
		<Name>NIP_ENERJI_DAGITIM_DEPOLAMA</Name>
		<UserStyle>
			<Title>NIP_ENERJI_DAGITIM_DEPOLAMA</Title>
			<FeatureTypeStyle>
				<Rule>
					<Name>0</Name>
					<Title>REGULATOR_ALANI</Title>
					<MaxScaleDenominator>80000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>EnerjiTesisTip</ogc:PropertyName>
							<ogc:Literal>RegulatorAlani</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:90f3e7d7-7ba3-4390-9e5a-1f726657bce0.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer>
						<Graphic>
							<Mark>
								<WellKnownName>ttf://nazim_imar_00#0x006e</WellKnownName>
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
					<Title>TURBIN_ALANI</Title>
					<MaxScaleDenominator>80000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>EnerjiTesisTip</ogc:PropertyName>
							<ogc:Literal>TurbinAlani</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:1587296d-f1d3-4abd-b366-21c95b943d74.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer>
						<Graphic>
							<Mark>
								<WellKnownName>ttf://nazim_imar_00#0x0056</WellKnownName>
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
					<Title>DOGALGAZ_ILETIM_DAGITIM_TESIS_ALANI</Title>
					<MaxScaleDenominator>80000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>EnerjiTesisTip</ogc:PropertyName>
							<ogc:Literal>DogalgazIletimDagitimTesisiAlani</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:607646e3-0e11-4009-821d-67a253ce023e.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer>
						<Graphic>
							<Mark>
								<WellKnownName>ttf://nazim_imar_00#0x0030</WellKnownName>
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
					<Title>YANICI_PARLAYICI_PATLAYICI_MADDE_URETIM_DEPO_ALANI</Title>
					<MaxScaleDenominator>80000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>EnerjiTesisTip</ogc:PropertyName>
							<ogc:Literal>YaniciParlayiciPatlayiciMaddeUretimDepoAlani</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:4fc48b15-ee7a-4c0e-9cff-ddd22a1a2d03.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer>
						<Graphic>
							<Mark>
								<WellKnownName>ttf://NIP_10_2#0x0064</WellKnownName>
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
					<Title>ENERJI_DEPOLAMA_ALANI</Title>
					<MaxScaleDenominator>80000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>EnerjiTesisTip</ogc:PropertyName>
							<ogc:Literal>EnerjiDepolamaAlani</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:05ccf278-682d-4c7c-abda-0eea676252ac.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer>
						<Graphic>
							<Mark>
								<WellKnownName>ttf://nazim_imar_00#0x0027</WellKnownName>
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
					<Title>RAFINERI_ALANI</Title>
					<MaxScaleDenominator>80000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>EnerjiTesisTip</ogc:PropertyName>
							<ogc:Literal>RafineriAlani</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:85bf2712-c8ac-4d54-bd37-b3b260f2ff8f.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer>
						<Graphic>
							<Mark>
								<WellKnownName>ttf://NIP_10_1#0x004e</WellKnownName>
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
					<Title>RAFINERI_PETROKIMYA_TESISI_ALANI</Title>
					<MaxScaleDenominator>80000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>EnerjiTesisTip</ogc:PropertyName>
							<ogc:Literal>RafineriPetroKimyaTesisiAlani</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<PolygonSymbolizer>
						<Fill>
							<GraphicFill>
								<Graphic>
									<ExternalGraphic>
										<OnlineResource xlink:type="simple" xlink:href="mpyy-tarama:616fdcca-d824-4c68-bc7b-262ac18aad63.png" />
										<Format>image/png</Format>
									</ExternalGraphic>
								</Graphic>
							</GraphicFill>
						</Fill>
					</PolygonSymbolizer>
					<PointSymbolizer>
						<Graphic>
							<Mark>
								<WellKnownName>ttf://nazim_imar_00#0x0078</WellKnownName>
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
          <Title>YED</Title>
          <ogc:Filter>
            <ogc:PropertyIsEqualTo>
              <ogc:PropertyName>EnerjiTesisTip</ogc:PropertyName>
              <ogc:Literal>YenilenebilirEnerjiKaynaginaDayaliUretimTesisAlani</ogc:Literal>
            </ogc:PropertyIsEqualTo>
          </ogc:Filter>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke-width">1.2</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8</Size>
                </Graphic>
              </GraphicFill>
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
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke-width">1.2</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>20</Size>
                  <Rotation>45.0</Rotation>
                </Graphic>
              </GraphicFill>
            </Fill>
            <Stroke>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource xlink:type="simple" xlink:href="mpyy-eksik-sembol:YenilenebilirEnerjiKaynaklarinaDayaliEnerjiUretimTesisAlani.svg" />
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