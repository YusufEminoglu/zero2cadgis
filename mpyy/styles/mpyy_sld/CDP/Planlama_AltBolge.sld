<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
	<NamedLayer>
		<Name>CDP_PLANLAMA_ALT_BOLGE</Name>
		<UserStyle>
			<Title>CDP_PLANLAMA_ALT_BOLGE</Title>
			<FeatureTypeStyle>
				<Rule>
					<Title>PLANLAMA ALT BÖLGE</Title>
					<LineSymbolizer>
						<Stroke>
							<CssParameter name="stroke">#ff0000</CssParameter>
							<CssParameter name="stroke-linecap">square</CssParameter>
							<CssParameter name="stroke-linejoin">bevel</CssParameter>
							<CssParameter name="stroke-dasharray">0.0 0.0</CssParameter>
						</Stroke>
					</LineSymbolizer>
					<LineSymbolizer>
						<Stroke>
							<GraphicStroke>
								<Graphic>
									<Mark>
										<WellKnownName>circle</WellKnownName>
										<Fill>
											<CssParameter name="fill">#ff0000</CssParameter>
										</Fill>
										<Stroke>
											<CssParameter name="stroke">#ff0000</CssParameter>
										</Stroke>
									</Mark>
									<Size>11</Size>
								</Graphic>
							</GraphicStroke>
							<CssParameter name="stroke-dasharray">6.0 9.0</CssParameter>
						</Stroke>
					</LineSymbolizer>
				</Rule>
			</FeatureTypeStyle>
		</UserStyle>
	</NamedLayer>
</StyledLayerDescriptor>