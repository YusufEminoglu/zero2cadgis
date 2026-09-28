<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
	<NamedLayer>
		<Name>NIP_SU_ULASIM_BAGLANTISI</Name>
		<UserStyle>
			<Title>NIP_SU_ULASIM_BAGLANTISI</Title>
			<FeatureTypeStyle>
				<Rule>
					<Name>water-link-80000-25000</Name>
					<Title>NIP_SU_ULASIM_BAGLANTISI - uzak olcek</Title>
					<MaxScaleDenominator>80000</MaxScaleDenominator>
					<MinScaleDenominator>25000</MinScaleDenominator>
					<LineSymbolizer>
						<Stroke>
							<CssParameter name="stroke">#004da8</CssParameter>
							<CssParameter name="stroke-width">1.6</CssParameter>
							<CssParameter name="stroke-linecap">round</CssParameter>
							<CssParameter name="stroke-dasharray">8 3.2 0.1 3.2</CssParameter>
						</Stroke>
					</LineSymbolizer>
				</Rule>
				<Rule>
					<Name>water-link-25000-5000</Name>
					<Title>NIP_SU_ULASIM_BAGLANTISI - yakin olcek</Title>
					<MaxScaleDenominator>25000</MaxScaleDenominator>
					<MinScaleDenominator>5000</MinScaleDenominator>
					<LineSymbolizer><Stroke>
						<CssParameter name="stroke">#004da8</CssParameter>
						<CssParameter name="stroke-width">2.4</CssParameter>
						<CssParameter name="stroke-linecap">round</CssParameter>
						<CssParameter name="stroke-dasharray">12 4.8 0.1 4.8</CssParameter>
					</Stroke></LineSymbolizer>
				</Rule>
				<Rule>
					<Name>water-link-5000</Name>
					<Title>NIP_SU_ULASIM_BAGLANTISI - cok yakin olcek</Title>
					<MaxScaleDenominator>5000</MaxScaleDenominator>
					<LineSymbolizer><Stroke>
						<CssParameter name="stroke">#004da8</CssParameter>
						<CssParameter name="stroke-width">3.4</CssParameter>
						<CssParameter name="stroke-linecap">round</CssParameter>
						<CssParameter name="stroke-dasharray">17 6.8 0.1 6.8</CssParameter>
					</Stroke></LineSymbolizer>
				</Rule>
			</FeatureTypeStyle>
		</UserStyle>
	</NamedLayer>
</StyledLayerDescriptor>