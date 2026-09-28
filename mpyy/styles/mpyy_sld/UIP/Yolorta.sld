<?xml version='1.0' encoding='utf-8'?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
	<NamedLayer>
		<Name>UIP_YOLORTA</Name>
		<UserStyle>
			<Title>UIP_YOLORTA</Title>
			<FeatureTypeStyle>
				<Rule>
					<Title>UIP_YOLORTA</Title>
					<MinScaleDenominator>0</MinScaleDenominator>
					<MaxScaleDenominator>2000</MaxScaleDenominator>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Label>(</Label>
						<Font>
							<CssParameter name="font-family">ESRI Default Marker</CssParameter>
							<CssParameter name="font-size">
								<ogc:Mul>
									<ogc:PropertyName>YolGenisligi</ogc:PropertyName>
									<ogc:Literal>2.5</ogc:Literal>
								 </ogc:Mul>
							</CssParameter>
							<CssParameter name="font-style">normal</CssParameter>
						</Font>
						<LabelPlacement>
							<PointPlacement>
								<AnchorPoint>
									<AnchorPointX>0.5</AnchorPointX>
									<AnchorPointY>0.5</AnchorPointY>
								</AnchorPoint>
							</PointPlacement>
						</LabelPlacement>
						<Fill>
							<CssParameter name="fill">#000000</CssParameter>
						</Fill>
						<VendorOption name="conflictResolution">false</VendorOption>
					</TextSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						
						<Geometry>
							<ogc:Function name="centroid">
								<ogc:PropertyName>geometry</ogc:PropertyName>
							</ogc:Function>
						</Geometry>
						<Label>
							<ogc:PropertyName>yol_genisligi1</ogc:PropertyName>
						</Label>
						<Font>
							<CssParameter name="font-family">DejaVu Sans</CssParameter>
							<CssParameter name="font-size">
								<ogc:Mul>
									<ogc:PropertyName>yol_genisligi3</ogc:PropertyName>
									<ogc:Literal>2.5</ogc:Literal>
								 </ogc:Mul>
							</CssParameter>
							<CssParameter name="font-style">normal</CssParameter>
						</Font>
						<LabelPlacement>
							<PointPlacement>
								<AnchorPoint>
									<AnchorPointX>0.8</AnchorPointX>
									<AnchorPointY>0.5</AnchorPointY>
								</AnchorPoint>
							</PointPlacement>
						</LabelPlacement>
						<Fill>
							<CssParameter name="fill">#000000</CssParameter>
						</Fill>
						<VendorOption name="conflictResolution">false</VendorOption>
					</TextSymbolizer>
					<TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
						<Geometry>
							<ogc:Function name="centroid">
								<ogc:PropertyName>geometry</ogc:PropertyName>
							</ogc:Function>
						</Geometry>
						<Label>
							<ogc:PropertyName>yol_genisligi2</ogc:PropertyName>
						</Label>
						<Font>
							<CssParameter name="font-family">DejaVu Sans</CssParameter>
							<CssParameter name="font-size">
								<ogc:Mul>
									<ogc:PropertyName>yol_genisligi4</ogc:PropertyName>
									<ogc:Literal>2.5</ogc:Literal>
								 </ogc:Mul>
							</CssParameter>
							<CssParameter name="font-style">normal</CssParameter>
						</Font>
						<LabelPlacement>
							<PointPlacement>
								<AnchorPoint>
									<AnchorPointX>-0.4</AnchorPointX>
									<AnchorPointY>0</AnchorPointY>
								</AnchorPoint>
							</PointPlacement>
						</LabelPlacement>
						<Fill>
							<CssParameter name="fill">#000000</CssParameter>
						</Fill>
						<VendorOption name="conflictResolution">false</VendorOption>
						<VendorOption name="underlineText">true</VendorOption>
					</TextSymbolizer>
				</Rule>
			</FeatureTypeStyle>
		</UserStyle>
	</NamedLayer>
</StyledLayerDescriptor>