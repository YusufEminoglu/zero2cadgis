<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
	<NamedLayer>
		<Name>NIP_KENTSEL_DONUSUM_SINIR</Name>
		<UserStyle>
			<Title>NIP_KENTSEL_DONUSUM_SINIR</Title>
			<FeatureTypeStyle>
				<Rule>
					<Name>0</Name>
					<Title>RISKLI_ALAN_SINIRI</Title>
					<MaxScaleDenominator>80000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>KentselDonusumSinirlariTip</ogc:PropertyName>
							<ogc:Literal>RiskliAlanSiniri</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<CssParameter name="stroke">#000000</CssParameter>
							<CssParameter name="stroke-width">0.3528</CssParameter>
							<CssParameter name="stroke-dasharray">5 1</CssParameter>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>RA</Label>
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
							<CssParameter name="fill">#000000</CssParameter>
						</Fill>
						<VendorOption name="conflictResolution">false</VendorOption>
						<VendorOption name="repeat">150</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>REZERV_YAPI_ALAN_SINIRI</Title>
					<MaxScaleDenominator>80000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>KentselDonusumSinirlariTip</ogc:PropertyName>
							<ogc:Literal>RezervYapiAlanSiniri</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<CssParameter name="stroke">#000000</CssParameter>
							<CssParameter name="stroke-width">0.3528</CssParameter>
							<CssParameter name="stroke-dasharray">5 1</CssParameter>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>RYA</Label>
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
							<CssParameter name="fill">#000000</CssParameter>
						</Fill>
						<VendorOption name="conflictResolution">false</VendorOption>
						<VendorOption name="repeat">150</VendorOption>
					</TextSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>YENILEME_ALAN_SINIRI</Title>
					<MaxScaleDenominator>80000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>KentselDonusumSinirlariTip</ogc:PropertyName>
							<ogc:Literal>YenilemeAlanSiniri</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<CssParameter name="stroke">#000000</CssParameter>
							<CssParameter name="stroke-width">0.3528</CssParameter>
							<CssParameter name="stroke-dasharray">5 1</CssParameter>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>YENİLEME</Label>
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
							<CssParameter name="fill">#000000</CssParameter>
						</Fill>
						<VendorOption name="conflictResolution">false</VendorOption>
						<VendorOption name="repeat">150</VendorOption>
					</TextSymbolizer>
				</Rule>
			</FeatureTypeStyle>
		</UserStyle>
	</NamedLayer>
</StyledLayerDescriptor>