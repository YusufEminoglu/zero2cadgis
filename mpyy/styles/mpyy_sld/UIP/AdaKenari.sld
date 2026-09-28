<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
	<NamedLayer>
		<Name>UIP_ADA_KENARI</Name>
		<UserStyle>
			<Title>UIP_ADA_KENARI</Title>
			<FeatureTypeStyle>
				<Rule>
					<Name>0</Name>
					<Title>KADEME_HATTI</Title>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>AdaKenariCizgiTip</ogc:PropertyName>
							<ogc:Literal>KademeHatti</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<MinScaleDenominator>0</MinScaleDenominator>
					<MaxScaleDenominator>5000</MaxScaleDenominator>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<CssParameter name="stroke">#000000</CssParameter>
							<CssParameter name="stroke-width">0.3528</CssParameter>
						</Stroke>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>ONERILEN</Title>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>AdaKenariCizgiTip</ogc:PropertyName>
							<ogc:Literal>Onerilen</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<MinScaleDenominator>0</MinScaleDenominator>
					<MaxScaleDenominator>5000</MaxScaleDenominator>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<CssParameter name="stroke">#000000</CssParameter>
							<CssParameter name="stroke-width">
								<ogc:PropertyName>CizgiKalinligi</ogc:PropertyName>
							</CssParameter>
						</Stroke>
						<PerpendicularOffset>
							<ogc:Mul>
								<ogc:PropertyName>CizgiKalinligi</ogc:PropertyName>
								<ogc:Literal>0.5</ogc:Literal>
							</ogc:Mul>
						</PerpendicularOffset>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>KORUNAN</Title>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>AdaKenariCizgiTip</ogc:PropertyName>
							<ogc:Literal>Korunan</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<MinScaleDenominator>0</MinScaleDenominator>
					<MaxScaleDenominator>5000</MaxScaleDenominator>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<CssParameter name="stroke">#000000</CssParameter>
							<CssParameter name="stroke-width">
								<ogc:PropertyName>CizgiKalinligi</ogc:PropertyName>
							</CssParameter>
							<CssParameter name="stroke-dasharray">0.575 0.575</CssParameter>
						</Stroke>
						<PerpendicularOffset>
							<ogc:Mul>
								<ogc:PropertyName>CizgiKalinligi</ogc:PropertyName>
								<ogc:Literal>0.5</ogc:Literal>
							</ogc:Mul>
						</PerpendicularOffset>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>DUZELTILEN</Title>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>AdaKenariCizgiTip</ogc:PropertyName>
							<ogc:Literal>Duzeltilen</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<MinScaleDenominator>0</MinScaleDenominator>
					<MaxScaleDenominator>5000</MaxScaleDenominator>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<CssParameter name="stroke">#000000</CssParameter>
							<CssParameter name="stroke-width">
								<ogc:PropertyName>CizgiKalinligi</ogc:PropertyName>
							</CssParameter>
							<CssParameter name="stroke-dasharray">2 0.6</CssParameter>
						</Stroke>
						<PerpendicularOffset>
							<ogc:Mul>
								<ogc:PropertyName>CizgiKalinligi</ogc:PropertyName>
								<ogc:Literal>0.5</ogc:Literal>
							</ogc:Mul>
						</PerpendicularOffset>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>IFRAZ_HATTI</Title>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>AdaKenariCizgiTip</ogc:PropertyName>
							<ogc:Literal>IfrazHatti</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<MinScaleDenominator>0</MinScaleDenominator>
					<MaxScaleDenominator>5000</MaxScaleDenominator>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<CssParameter name="stroke">#000000</CssParameter>
							<CssParameter name="stroke-width">0.3528</CssParameter>
							<CssParameter name="stroke-dasharray">2 2</CssParameter>
						</Stroke>
					</LineSymbolizer>
				</Rule>
			</FeatureTypeStyle>
		</UserStyle>
	</NamedLayer>
</StyledLayerDescriptor>