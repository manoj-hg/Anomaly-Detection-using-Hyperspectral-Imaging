"""
Automated PDF Report Generation Module
Generates comprehensive PDF reports for anomaly detection results
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import base64
import io
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not installed. Install with: pip install reportlab")


class PDFReportGenerator:
    """
    Generates PDF reports for anomaly detection results
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        if not REPORTLAB_AVAILABLE:
            return
            
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#764ba2'),
            spaceAfter=20
        ))
        
        # Body style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            leading=14
        ))
        
        # Header style
        self.styles.add(ParagraphStyle(
            name='CustomHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=10,
            spaceBefore=20
        ))
    
    def generate_report(
        self,
        results: Dict,
        images: Dict[str, np.ndarray],
        output_path: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Generate comprehensive PDF report
        
        Args:
            results: Detection results dictionary
            images: Dictionary of result images
            output_path: Path to save PDF
            metadata: Optional metadata (location, timestamp, etc.)
            
        Returns:
            Path to generated PDF
        """
        if not REPORTLAB_AVAILABLE:
            print("ReportLab not available, cannot generate PDF")
            return ""
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build story
        story = []
        
        # Title page
        story.extend(self._create_title_page(metadata))
        story.append(PageBreak())
        
        # Executive summary
        story.extend(self._create_executive_summary(results, metadata))
        story.append(PageBreak())
        
        # Detection results
        story.extend(self._create_detection_results(results))
        story.append(PageBreak())
        
        # Visualizations
        story.extend(self._create_visualizations(images))
        story.append(PageBreak())
        
        # Statistics
        story.extend(self._create_statistics(results))
        story.append(PageBreak())
        
        # Recommendations
        story.extend(self._create_recommendations(results))
        
        # Build PDF
        doc.build(story)
        
        return output_path
    
    def _create_title_page(self, metadata: Optional[Dict]) -> List:
        """Create title page"""
        story = []
        
        # Title
        story.append(Paragraph("Geospatial Anomaly Detection Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5 * inch))
        
        # Subtitle
        story.append(Paragraph("AI-Powered Spectral Analysis", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 1 * inch))
        
        # Metadata table
        if metadata:
            data = [
                ['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                ['Location:', f"{metadata.get('lat', 'N/A')}, {metadata.get('lon', 'N/A')}"],
                ['Data Source:', metadata.get('data_source', 'N/A')],
                ['Model:', metadata.get('model', 'Ensemble')]
            ]
            
            table = Table(data, colWidths=[2 * inch, 3 * inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (1, 0), (1, -1), colors.whitesmoke),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
            ]))
            story.append(table)
        
        story.append(Spacer(1, 2 * inch))
        
        # Disclaimer
        story.append(Paragraph(
            "This report was generated automatically by the AI-Powered Geospatial Anomaly Detection System. "
            "Results should be verified by domain experts before making critical decisions.",
            self.styles['CustomBody']
        ))
        
        return story
    
    def _create_executive_summary(self, results: Dict, metadata: Optional[Dict]) -> List:
        """Create executive summary section"""
        story = []
        
        story.append(Paragraph("Executive Summary", self.styles['CustomHeader']))
        
        # Summary statistics
        anomaly_count = results.get('anomaly_count', 0)
        anomaly_percentage = results.get('anomaly_percentage', 0)
        
        summary_text = f"""
        The anomaly detection analysis identified <b>{anomaly_count}</b> anomalous pixels, 
        representing <b>{anomaly_percentage:.2f}%</b> of the total analyzed area. 
        The detection was performed using an ensemble of machine learning models including 
        Isolation Forest and Autoencoder approaches.
        """
        
        story.append(Paragraph(summary_text, self.styles['CustomBody']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Key findings
        story.append(Paragraph("Key Findings:", self.styles['CustomHeader']))
        
        findings = [
            f"• Total anomalies detected: {anomaly_count}",
            f"• Anomaly density: {anomaly_percentage:.2f}%",
            f"• Isolation Forest threshold: {results.get('iso_threshold', 0):.4f}",
            f"• Autoencoder threshold: {results.get('ae_threshold', 0):.4f}",
            f"• Fused threshold: {results.get('fused_threshold', 0):.4f}"
        ]
        
        for finding in findings:
            story.append(Paragraph(finding, self.styles['CustomBody']))
        
        return story
    
    def _create_detection_results(self, results: Dict) -> List:
        """Create detection results section"""
        story = []
        
        story.append(Paragraph("Detection Results", self.styles['CustomHeader']))
        
        # Results table
        data = [
            ['Metric', 'Value'],
            ['Data Source', results.get('data_source', 'N/A')],
            ['Anomaly Count', str(results.get('anomaly_count', 0))],
            ['Anomaly Percentage', f"{results.get('anomaly_percentage', 0):.2f}%"],
            ['Isolation Forest Threshold', f"{results.get('iso_threshold', 0):.4f}"],
            ['Autoencoder Threshold', f"{results.get('ae_threshold', 0):.4f}"],
            ['Fused Threshold', f"{results.get('fused_threshold', 0):.4f}"]
        ]
        
        table = Table(data, colWidths=[2.5 * inch, 2.5 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(table)
        
        return story
    
    def _create_visualizations(self, images: Dict[str, np.ndarray]) -> List:
        """Create visualizations section"""
        story = []
        
        story.append(Paragraph("Visualizations", self.styles['CustomHeader']))
        
        # Add images if available
        image_order = ['rgb', 'heatmap', 'overlay', 'binary']
        
        for img_type in image_order:
            if img_type in images:
                img_array = images[img_type]
                
                # Convert to base64
                if img_array.dtype != np.uint8:
                    img_array = (img_array * 255).astype(np.uint8)
                
                # Create PIL image
                try:
                    from PIL import Image as PILImage
                    pil_img = PILImage.fromarray(img_array)
                    
                    # Resize if too large
                    if pil_img.size[0] > 400:
                        pil_img = pil_img.resize((400, int(400 * pil_img.size[1] / pil_img.size[0])))
                    
                    # Save to buffer
                    img_buffer = io.BytesIO()
                    pil_img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    
                    # Add to story
                    img = Image(img_buffer, width=4 * inch)
                    story.append(img)
                    story.append(Paragraph(f"{img_type.upper()} View", self.styles['CustomBody']))
                    story.append(Spacer(1, 0.2 * inch))
                    
                except Exception as e:
                    print(f"Error adding image {img_type}: {e}")
        
        return story
    
    def _create_statistics(self, results: Dict) -> List:
        """Create statistics section"""
        story = []
        
        story.append(Paragraph("Statistical Analysis", self.styles['CustomHeader']))
        
        # Spectral band statistics
        if 'spectral_bands' in results:
            spectral_stats = results['spectral_bands']
            
            for model_name, stats in spectral_stats.items():
                story.append(Paragraph(f"{model_name.upper()} Statistics:", self.styles['CustomHeader']))
                
                data = [
                    ['Statistic', 'Value'],
                    ['Min', f"{stats.get('min', 0):.4f}"],
                    ['Max', f"{stats.get('max', 0):.4f}"],
                    ['Mean', f"{stats.get('mean', 0):.4f}"],
                    ['Std Dev', f"{stats.get('std', 0):.4f}"]
                ]
                
                table = Table(data, colWidths=[2 * inch, 2 * inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#764ba2')),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                story.append(table)
                story.append(Spacer(1, 0.2 * inch))
        
        return story
    
    def _create_recommendations(self, results: Dict) -> List:
        """Create recommendations section"""
        story = []
        
        story.append(Paragraph("Recommendations", self.styles['CustomHeader']))
        
        anomaly_percentage = results.get('anomaly_percentage', 0)
        
        if anomaly_percentage < 5:
            recommendation = "Low anomaly density detected. Area appears normal with minimal anomalies."
        elif anomaly_percentage < 15:
            recommendation = "Moderate anomaly density detected. Further investigation recommended for affected areas."
        elif anomaly_percentage < 30:
            recommendation = "High anomaly density detected. Significant anomalies present requiring detailed analysis."
        else:
            recommendation = "Very high anomaly density detected. Critical anomalies requiring immediate attention."
        
        story.append(Paragraph(recommendation, self.styles['CustomBody']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Additional recommendations
        additional = [
            "• Verify results with ground truth data if available",
            "• Consider temporal analysis to identify changes over time",
            "• Cross-reference with other data sources (e.g., weather, human activity)",
            "• Consult domain experts for interpretation of anomaly patterns"
        ]
        
        for rec in additional:
            story.append(Paragraph(rec, self.styles['CustomBody']))
        
        return story


class DataExporter:
    """
    Export detection results in various formats
    """
    
    def __init__(self):
        pass
    
    def export_csv(
        self,
        results: Dict,
        output_path: str
    ) -> str:
        """
        Export results to CSV format
        
        Args:
            results: Detection results
            output_path: Path to save CSV
            
        Returns:
            Path to saved file
        """
        import csv
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['Metric', 'Value'])
            
            # Write data
            writer.writerow(['Data Source', results.get('data_source', 'N/A')])
            writer.writerow(['Anomaly Count', results.get('anomaly_count', 0)])
            writer.writerow(['Anomaly Percentage', f"{results.get('anomaly_percentage', 0):.4f}"])
            writer.writerow(['Isolation Forest Threshold', f"{results.get('iso_threshold', 0):.4f}"])
            writer.writerow(['Autoencoder Threshold', f"{results.get('ae_threshold', 0):.4f}"])
            writer.writerow(['Fused Threshold', f"{results.get('fused_threshold', 0):.4f}"])
        
        return output_path
    
    def export_json(
        self,
        results: Dict,
        output_path: str
    ) -> str:
        """
        Export results to JSON format
        
        Args:
            results: Detection results
            output_path: Path to save JSON
            
        Returns:
            Path to saved file
        """
        import json
        
        # Convert numpy types to Python types
        serializable_results = {}
        for key, value in results.items():
            if isinstance(value, np.ndarray):
                serializable_results[key] = value.tolist()
            elif isinstance(value, (np.integer, np.floating)):
                serializable_results[key] = float(value)
            else:
                serializable_results[key] = value
        
        with open(output_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        return output_path
    
    def export_geotiff(
        self,
        data: np.ndarray,
        output_path: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Export data to GeoTIFF format
        
        Args:
            data: (H, W) or (H, W, C) array
            output_path: Path to save GeoTIFF
            metadata: Optional geospatial metadata
            
        Returns:
            Path to saved file
        """
        try:
            import rasterio
            from rasterio.transform import from_bounds
            
            # Ensure 2D or 3D
            if len(data.shape) == 3:
                data = data.mean(axis=-1)
            
            # Default metadata if not provided
            if metadata is None:
                metadata = {
                    'bounds': (-180, -90, 180, 90),
                    'crs': 'EPSG:4326'
                }
            
            # Create transform
            transform = from_bounds(
                metadata['bounds'][0],
                metadata['bounds'][1],
                metadata['bounds'][2],
                metadata['bounds'][3],
                data.shape[1],
                data.shape[0]
            )
            
            # Write GeoTIFF
            with rasterio.open(
                output_path,
                'w',
                driver='GTiff',
                height=data.shape[0],
                width=data.shape[1],
                count=1,
                dtype=data.dtype,
                crs=metadata.get('crs', 'EPSG:4326'),
                transform=transform
            ) as dst:
                dst.write(data, 1)
            
            return output_path
            
        except ImportError:
            print("rasterio not installed. Install with: pip install rasterio")
            return ""


if __name__ == "__main__":
    print("Testing PDF Report Generation...")
    
    if REPORTLAB_AVAILABLE:
        generator = PDFReportGenerator()
        
        # Create dummy results
        results = {
            'data_source': 'Sentinel-2',
            'anomaly_count': 1234,
            'anomaly_percentage': 12.34,
            'iso_threshold': 0.5678,
            'ae_threshold': 0.3456,
            'fused_threshold': 0.4567,
            'spectral_bands': {
                'iso_scores': {'min': 0.1, 'max': 0.9, 'mean': 0.5, 'std': 0.2},
                'ae_scores': {'min': 0.05, 'max': 0.85, 'mean': 0.45, 'std': 0.18}
            }
        }
        
        # Create dummy images
        images = {
            'rgb': np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8),
            'heatmap': np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        }
        
        # Create metadata
        metadata = {
            'lat': 40.7128,
            'lon': -74.0060,
            'data_source': 'Sentinel-2',
            'model': 'Ensemble'
        }
        
        # Generate report
        output_path = 'test_report.pdf'
        generator.generate_report(results, images, output_path, metadata)
        print(f"Report generated: {output_path}")
        
        # Test data export
        exporter = DataExporter()
        exporter.export_csv(results, 'test_results.csv')
        exporter.export_json(results, 'test_results.json')
        print("CSV and JSON exports created")
        
    else:
        print("ReportLab not available, skipping PDF generation test")
    
    print("Report generation test complete!")
