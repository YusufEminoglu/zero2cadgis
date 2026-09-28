<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
	<NamedLayer>
		<Name>UIP_YAPI_YAKLASMA_MES</Name>
		<UserStyle>
			<Name>UIP_YAPI_YAKLASMA_MES</Name>
			<FeatureTypeStyle>
				<Rule>
					<MaxScaleDenominator>75000</MaxScaleDenominator>
					<Name>Single symbol</Name>
					<LineSymbolizer>
						<Stroke>
							<CssParameter name="stroke">#000000</CssParameter>
							<CssParameter name="stroke-width">1</CssParameter>
							<CssParameter name="stroke-linejoin">bevel</CssParameter>
							<CssParameter name="stroke-linecap">square</CssParameter>
						</Stroke>
					</LineSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>
							<ogc:Function name="if_then_else">
								<ogc:Function name="greaterThan">
									<ogc:PropertyName>Mesafe</ogc:PropertyName>
									<ogc:Literal>0</ogc:Literal>
								</ogc:Function>
								<ogc:PropertyName>Mesafe</ogc:PropertyName>
								<ogc:Literal />
							</ogc:Function>
						</Label>
						<Font>
							<CssParameter name="font-family">Microsoft Sans Serif</CssParameter>
							<CssParameter name="font-size">5</CssParameter>
						</Font>
						<LabelPlacement>
							<LinePlacement>
								<GeneralizeLine>true</GeneralizeLine>
							</LinePlacement>
						</LabelPlacement>
						<Fill>
							<CssParameter name="fill">#000000</CssParameter>
						</Fill>
					</TextSymbolizer>
				</Rule>
			</FeatureTypeStyle>
		</UserStyle>
	</NamedLayer>
</StyledLayerDescriptor>