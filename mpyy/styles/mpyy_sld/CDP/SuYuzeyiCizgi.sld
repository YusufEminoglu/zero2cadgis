<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
	<NamedLayer>
		<Name>CDP_SU_YUZEYI_CIZGI</Name>
		<UserStyle>
			<Title>CDP_SU_YUZEYI_CIZGI</Title>
			<FeatureTypeStyle>
				<Rule>
					<Name>0</Name>
					<Title>AKARSU_NEHIR_DERE</Title>
					<MaxScaleDenominator>500000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>SuYuzeyiCizgiTip</ogc:PropertyName>
							<ogc:Literal>AkarsuNehirDere</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<CssParameter name="stroke">#73DFEB</CssParameter>
							<CssParameter name="stroke-width">2.8344672</CssParameter>
						</Stroke>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>KANAL_KANALET</Title>
					<MaxScaleDenominator>500000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>SuYuzeyiCizgiTip</ogc:PropertyName>
							<ogc:Literal>KanalKanalet</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<CssParameter name="stroke">#73DFEB</CssParameter>
							<CssParameter name="stroke-width">2.8344672</CssParameter>
						</Stroke>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>0</Name>
					<Title>SULAMA_KANALI</Title>
					<MaxScaleDenominator>500000</MaxScaleDenominator>
					<ogc:Filter>
						<ogc:PropertyIsEqualTo>
							<ogc:PropertyName>SuYuzeyiCizgiTip</ogc:PropertyName>
							<ogc:Literal>SulamaKanali</ogc:Literal>
						</ogc:PropertyIsEqualTo>
					</ogc:Filter>
					<LineSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Stroke>
							<CssParameter name="stroke">#73DFEB</CssParameter>
							<CssParameter name="stroke-width">2.8344672</CssParameter>
						</Stroke>
					</LineSymbolizer>
				</Rule>
			</FeatureTypeStyle>
		</UserStyle>
	</NamedLayer>
</StyledLayerDescriptor>