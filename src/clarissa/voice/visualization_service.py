"""
Visualization Service for CLARISSA Voice Interface.

Maps voice command intents to ReservoirVisualizer3D functions.
Handles data loading, parameter mapping, and error handling.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, Union
from enum import Enum
import numpy as np


class PropertyType(Enum):
    """Supported reservoir properties."""
    PERMEABILITY = "permeability"
    POROSITY = "porosity"
    WATER_SATURATION = "water_saturation"
    OIL_SATURATION = "oil_saturation"
    PRESSURE = "pressure"
    NET_TO_GROSS = "ntg"


class ViewType(Enum):
    """Supported visualization views."""
    VIEW_3D = "3d"
    CROSS_SECTION_XY = "cross_section_xy"
    CROSS_SECTION_XZ = "cross_section_xz"
    CROSS_SECTION_YZ = "cross_section_yz"
    ANIMATION = "animation"


@dataclass
class VisualizationResult:
    """Result of a visualization operation."""
    success: bool
    figure: Any = None  # Plotly figure
    html: Optional[str] = None  # HTML representation
    image_bytes: Optional[bytes] = None  # PNG bytes
    gif_path: Optional[str] = None  # Path to GIF file
    error: Optional[str] = None
    description: str = ""
    render_time_ms: float = 0.0


@dataclass
class ModelData:
    """Container for reservoir model data."""
    nx: int
    ny: int
    nz: int
    dx: float = 100.0
    dy: float = 100.0
    dz: float = 10.0
    
    # Static properties (shape: nx, ny, nz)
    permeability: Optional[np.ndarray] = None
    porosity: Optional[np.ndarray] = None
    ntg: Optional[np.ndarray] = None
    
    # Dynamic properties (list of timesteps, each shape: nx, ny, nz)
    water_saturation: Optional[List[np.ndarray]] = None
    oil_saturation: Optional[List[np.ndarray]] = None
    pressure: Optional[List[np.ndarray]] = None
    
    # Time information
    times_days: Optional[List[float]] = None
    
    # Metadata
    model_name: str = "Unknown"
    units: Dict[str, str] = field(default_factory=lambda: {
        "permeability": "mD",
        "porosity": "fraction",
        "water_saturation": "fraction",
        "pressure": "bar"
    })


# Default colorscales for properties
PROPERTY_COLORSCALES = {
    PropertyType.PERMEABILITY: "Viridis",
    PropertyType.POROSITY: "Blues",
    PropertyType.WATER_SATURATION: "RdYlBu_r",
    PropertyType.OIL_SATURATION: "YlOrRd",
    PropertyType.PRESSURE: "Plasma",
    PropertyType.NET_TO_GROSS: "Greens",
}

PROPERTY_TITLES = {
    PropertyType.PERMEABILITY: "Permeability (mD)",
    PropertyType.POROSITY: "Porosity (fraction)",
    PropertyType.WATER_SATURATION: "Water Saturation (Sw)",
    PropertyType.OIL_SATURATION: "Oil Saturation (So)",
    PropertyType.PRESSURE: "Pressure (bar)",
    PropertyType.NET_TO_GROSS: "Net-to-Gross",
}


class VisualizationService:
    """
    Service for creating reservoir visualizations from voice commands.
    
    Example:
        service = VisualizationService()
        service.load_model(model_data)
        
        # From voice intent
        result = await service.visualize(
            property="permeability",
            view_type="3d",
            layer=5,
            time_days=100
        )
    """
    
    def __init__(self, model_data: Optional[ModelData] = None):
        """Initialize the visualization service."""
        self.model_data = model_data
        self._visualizer = None
        self._loading = False
        self._last_figure = None
        
        # Callbacks for UI integration
        self._on_loading_start: Optional[Callable] = None
        self._on_loading_end: Optional[Callable] = None
        self._on_error: Optional[Callable[[str], None]] = None
    
    def load_model(self, model_data: ModelData) -> None:
        """Load model data for visualization."""
        self.model_data = model_data
        self._visualizer = self._create_visualizer()
    
    def _create_visualizer(self):
        """Create ReservoirVisualizer3D instance."""
        if not self.model_data:
            return None
        
        # Import here to avoid dependency issues
        try:
            from .viz_3d import ReservoirVisualizer3D
        except ImportError:
            # Fallback inline definition
            return self._create_inline_visualizer()
        
        return ReservoirVisualizer3D(
            nx=self.model_data.nx,
            ny=self.model_data.ny,
            nz=self.model_data.nz,
            dx=self.model_data.dx,
            dy=self.model_data.dy,
            dz=self.model_data.dz
        )
    
    def _create_inline_visualizer(self):
        """Create visualizer without external import."""
        import plotly.graph_objects as go
        import plotly.express as px
        
        model = self.model_data
        
        class InlineVisualizer:
            def __init__(self):
                self.nx, self.ny, self.nz = model.nx, model.ny, model.nz
                self.dx, self.dy, self.dz = model.dx, model.dy, model.dz
                self.x = np.arange(self.nx) * self.dx
                self.y = np.arange(self.ny) * self.dy
                self.z = np.arange(self.nz) * self.dz
            
            def plot_property_3d(self, prop_3d, title, colorscale='Viridis', 
                                 opacity=0.6, show_wells=True):
                X, Y, Z = np.meshgrid(
                    self.x + self.dx/2,
                    self.y + self.dy/2,
                    self.z + self.dz/2,
                    indexing='ij'
                )
                
                x_flat, y_flat, z_flat = X.flatten(), Y.flatten(), Z.flatten()
                values = prop_3d.flatten()
                mask = values > np.percentile(values, 5)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter3d(
                    x=x_flat[mask], y=y_flat[mask], z=-z_flat[mask],
                    mode='markers',
                    marker=dict(size=4, color=values[mask], colorscale=colorscale,
                               opacity=opacity, colorbar=dict(title='')),
                ))
                
                fig.update_layout(
                    title=dict(text=f'🎲 {title}', font=dict(size=20)),
                    scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)',
                              zaxis_title='Depth (m)', aspectmode='data'),
                    width=800, height=600,
                )
                return fig
            
            def plot_cross_section_xy(self, prop_3d, layer_k, title, colorscale='Viridis'):
                layer_data = prop_3d[:, :, layer_k]
                depth = self.z[layer_k] + self.dz/2
                
                fig = px.imshow(
                    layer_data.T, x=self.x + self.dx/2, y=self.y + self.dy/2,
                    origin='lower', color_continuous_scale=colorscale, aspect='equal'
                )
                fig.update_layout(
                    title=f'📊 {title} - Layer {layer_k+1} (Depth: {depth:.0f}m)',
                    width=700, height=600
                )
                return fig
            
            def plot_cross_section_xz(self, prop_3d, j_slice, title, colorscale='Viridis'):
                slice_data = prop_3d[:, j_slice, :]
                y_pos = self.y[j_slice] + self.dy/2
                
                fig = px.imshow(
                    slice_data.T, x=self.x + self.dx/2, y=-(self.z + self.dz/2),
                    origin='upper', color_continuous_scale=colorscale, aspect='auto'
                )
                fig.update_layout(
                    title=f'📊 {title} - Y={y_pos:.0f}m',
                    width=800, height=400
                )
                return fig
            
            def create_saturation_animation(self, saturation_over_time, times):
                X, Y, Z = np.meshgrid(
                    self.x + self.dx/2, self.y + self.dy/2, self.z + self.dz/2,
                    indexing='ij'
                )
                x_flat, y_flat, z_flat = X.flatten(), Y.flatten(), Z.flatten()
                
                frames = []
                for i, (sat, time) in enumerate(zip(saturation_over_time, times)):
                    values = sat.flatten()
                    frames.append(go.Frame(
                        data=[go.Scatter3d(
                            x=x_flat, y=y_flat, z=-z_flat, mode='markers',
                            marker=dict(size=4, color=values, colorscale='RdYlBu_r',
                                       cmin=0, cmax=1, opacity=0.7),
                        )],
                        name=str(i)
                    ))
                
                fig = go.Figure(
                    data=[go.Scatter3d(
                        x=x_flat, y=y_flat, z=-z_flat, mode='markers',
                        marker=dict(size=4, color=saturation_over_time[0].flatten(),
                                   colorscale='RdYlBu_r', cmin=0, cmax=1, opacity=0.7,
                                   colorbar=dict(title='Sw')),
                    )],
                    frames=frames
                )
                
                fig.update_layout(
                    title='🌊 Water Saturation Evolution',
                    scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)',
                              zaxis_title='Depth (m)', aspectmode='data'),
                    updatemenus=[dict(
                        type='buttons', showactive=False, y=0, x=0.1,
                        buttons=[
                            dict(label='▶️ Play', method='animate',
                                 args=[None, dict(frame=dict(duration=500, redraw=True))]),
                            dict(label='⏸️ Pause', method='animate',
                                 args=[[None], dict(frame=dict(duration=0), mode='immediate')])
                        ]
                    )],
                    width=800, height=650,
                )
                return fig
        
        return InlineVisualizer()
    
    def set_callbacks(
        self,
        on_loading_start: Optional[Callable] = None,
        on_loading_end: Optional[Callable] = None,
        on_error: Optional[Callable[[str], None]] = None
    ) -> None:
        """Set UI callbacks for loading indicators."""
        self._on_loading_start = on_loading_start
        self._on_loading_end = on_loading_end
        self._on_error = on_error
    
    async def visualize(
        self,
        property: str,
        view_type: str = "3d",
        layer: Optional[int] = None,
        time_days: Optional[float] = None,
        colorscale: Optional[str] = None,
        **kwargs
    ) -> VisualizationResult:
        """
        Create visualization from voice command parameters.
        
        Args:
            property: Property to visualize (permeability, porosity, etc.)
            view_type: View type (3d, cross_section_xy, animation, etc.)
            layer: Layer index (1-based, converted to 0-based internally)
            time_days: Time in days for dynamic properties
            colorscale: Optional Plotly colorscale override
            
        Returns:
            VisualizationResult with figure and metadata
        """
        import time
        start_time = time.time()
        
        # Notify loading start
        self._loading = True
        if self._on_loading_start:
            self._on_loading_start()
        
        try:
            # Validate model is loaded
            if not self.model_data or not self._visualizer:
                return VisualizationResult(
                    success=False,
                    error="No model loaded. Please load a reservoir model first.",
                    description="Model not available"
                )
            
            # Parse property type
            try:
                prop_type = PropertyType(property.lower().replace(" ", "_"))
            except ValueError:
                return VisualizationResult(
                    success=False,
                    error=f"Unknown property: {property}. Supported: permeability, porosity, water_saturation, oil_saturation, pressure",
                    description=f"Invalid property: {property}"
                )
            
            # Parse view type
            try:
                view = ViewType(view_type.lower().replace("-", "_"))
            except ValueError:
                view = ViewType.VIEW_3D  # Default to 3D
            
            # Get property data
            prop_data = self._get_property_data(prop_type, time_days)
            if prop_data is None:
                return VisualizationResult(
                    success=False,
                    error=f"Property data not available: {property}",
                    description=f"{property} data not found"
                )
            
            # Get colorscale
            cs = colorscale or PROPERTY_COLORSCALES.get(prop_type, "Viridis")
            title = PROPERTY_TITLES.get(prop_type, property)
            
            # Create visualization based on view type
            fig = await self._create_figure(view, prop_type, prop_data, layer, title, cs)
            
            if fig is None:
                return VisualizationResult(
                    success=False,
                    error="Failed to create visualization",
                    description="Visualization error"
                )
            
            # Store for potential export
            self._last_figure = fig
            
            render_time = (time.time() - start_time) * 1000
            
            # Build description
            description = self._build_description(prop_type, view, layer, time_days)
            
            return VisualizationResult(
                success=True,
                figure=fig,
                html=fig.to_html(include_plotlyjs='cdn', full_html=False),
                description=description,
                render_time_ms=render_time
            )
            
        except Exception as e:
            error_msg = str(e)
            if self._on_error:
                self._on_error(error_msg)
            return VisualizationResult(
                success=False,
                error=error_msg,
                description="Visualization failed"
            )
        
        finally:
            self._loading = False
            if self._on_loading_end:
                self._on_loading_end()
    
    def _get_property_data(
        self,
        prop_type: PropertyType,
        time_days: Optional[float] = None
    ) -> Optional[np.ndarray]:
        """Get property data array."""
        model = self.model_data
        
        if prop_type == PropertyType.PERMEABILITY:
            return model.permeability
        elif prop_type == PropertyType.POROSITY:
            return model.porosity
        elif prop_type == PropertyType.NET_TO_GROSS:
            return model.ntg
        elif prop_type == PropertyType.WATER_SATURATION:
            return self._get_timestep_data(model.water_saturation, time_days)
        elif prop_type == PropertyType.OIL_SATURATION:
            return self._get_timestep_data(model.oil_saturation, time_days)
        elif prop_type == PropertyType.PRESSURE:
            return self._get_timestep_data(model.pressure, time_days)
        
        return None
    
    def _get_timestep_data(
        self,
        data_list: Optional[List[np.ndarray]],
        time_days: Optional[float]
    ) -> Optional[np.ndarray]:
        """Get data at specific timestep."""
        if not data_list or len(data_list) == 0:
            return None
        
        if time_days is None:
            # Return last timestep
            return data_list[-1]
        
        if not self.model_data.times_days:
            return data_list[-1]
        
        # Find closest timestep
        times = self.model_data.times_days
        idx = min(range(len(times)), key=lambda i: abs(times[i] - time_days))
        
        return data_list[idx]
    
    async def _create_figure(
        self,
        view: ViewType,
        prop_type: PropertyType,
        prop_data: np.ndarray,
        layer: Optional[int],
        title: str,
        colorscale: str
    ):
        """Create Plotly figure based on view type."""
        viz = self._visualizer
        
        # Convert 1-based layer to 0-based
        layer_idx = (layer - 1) if layer else self.model_data.nz // 2
        layer_idx = max(0, min(layer_idx, self.model_data.nz - 1))
        
        if view == ViewType.VIEW_3D:
            return viz.plot_property_3d(prop_data, title, colorscale)
        
        elif view == ViewType.CROSS_SECTION_XY:
            return viz.plot_cross_section_xy(prop_data, layer_idx, title, colorscale)
        
        elif view == ViewType.CROSS_SECTION_XZ:
            j_slice = self.model_data.ny // 2
            return viz.plot_cross_section_xz(prop_data, j_slice, title, colorscale)
        
        elif view == ViewType.CROSS_SECTION_YZ:
            if hasattr(viz, 'plot_cross_section_yz'):
                i_slice = self.model_data.nx // 2
                return viz.plot_cross_section_yz(prop_data, i_slice, title, colorscale)
            return viz.plot_property_3d(prop_data, title, colorscale)
        
        elif view == ViewType.ANIMATION:
            # For animation, we need the full timeseries
            if prop_type == PropertyType.WATER_SATURATION and self.model_data.water_saturation:
                return viz.create_saturation_animation(
                    self.model_data.water_saturation,
                    self.model_data.times_days or list(range(len(self.model_data.water_saturation)))
                )
            # Fallback to static 3D
            return viz.plot_property_3d(prop_data, title, colorscale)
        
        return None
    
    def _build_description(
        self,
        prop_type: PropertyType,
        view: ViewType,
        layer: Optional[int],
        time_days: Optional[float]
    ) -> str:
        """Build human-readable description."""
        parts = [f"Showing {prop_type.value.replace('_', ' ')}"]
        
        if view == ViewType.CROSS_SECTION_XY and layer:
            parts.append(f"at layer {layer}")
        elif view == ViewType.CROSS_SECTION_XZ:
            parts.append("(vertical cross-section)")
        elif view == ViewType.ANIMATION:
            parts.append("animation")
        else:
            parts.append("in 3D")
        
        if time_days:
            parts.append(f"at day {time_days:.0f}")
        
        return " ".join(parts) + "."
    
    async def export_gif(
        self,
        filename: str = "animation.gif",
        fps: int = 2
    ) -> VisualizationResult:
        """Export current animation as GIF."""
        if not self._visualizer or not self.model_data:
            return VisualizationResult(
                success=False,
                error="No model loaded"
            )
        
        if not self.model_data.water_saturation:
            return VisualizationResult(
                success=False,
                error="No saturation data for animation"
            )
        
        try:
            if hasattr(self._visualizer, 'export_animation_gif'):
                path = self._visualizer.export_animation_gif(
                    self.model_data.water_saturation,
                    self.model_data.times_days or list(range(len(self.model_data.water_saturation))),
                    filename=filename,
                    fps=fps
                )
                return VisualizationResult(
                    success=True,
                    gif_path=path,
                    description=f"Animation exported to {filename}"
                )
            else:
                return VisualizationResult(
                    success=False,
                    error="GIF export not available"
                )
        except Exception as e:
            return VisualizationResult(
                success=False,
                error=str(e)
            )
    
    @property
    def is_loading(self) -> bool:
        """Check if visualization is currently rendering."""
        return self._loading
    
    @property
    def has_model(self) -> bool:
        """Check if model data is loaded."""
        return self.model_data is not None


# Convenience function for quick visualization from intent
async def visualize_from_intent(
    intent_slots: Dict[str, Any],
    service: VisualizationService
) -> VisualizationResult:
    """
    Create visualization directly from intent slots.
    
    Args:
        intent_slots: Slots from parsed intent
        service: VisualizationService instance
        
    Returns:
        VisualizationResult
    """
    return await service.visualize(
        property=intent_slots.get("property", "permeability"),
        view_type=intent_slots.get("view_type", "3d"),
        layer=intent_slots.get("layer"),
        time_days=intent_slots.get("time_days"),
    )