import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import matplotlib
import sys
import unittest
from unittest.mock import patch, MagicMock

# Try multiple interactive backends in order of preference
def setup_interactive_backend():
    backends_to_try = ['Qt5Agg', 'TkAgg', 'QtAgg', 'WebAgg', 'Gtk3Agg']
    for backend in backends_to_try:
        try:
            matplotlib.use(backend, force=True)
            print(f"Using {backend} backend for interactive plots")
            return True
        except Exception:
            continue
    
    # If all interactive backends fail, use a non-interactive one but warn the user
    matplotlib.use('Agg')
    print("Warning: No interactive backend available. Using non-interactive Agg backend.")
    print("Try installing one of these packages: PyQt5, tkinter, PySide2, or PyGObject")
    return False

# Set up the backend
is_interactive = setup_interactive_backend()

# Lorenz system parameters
sigma = 10
rho = 28
beta = 8/3

# Function to compute the derivatives
def lorenz_deriv(xyz, t0, sigma=sigma, beta=beta, rho=rho):
    x, y, z = xyz
    return [
        sigma * (y - x),
        x * (rho - z) - y,
        x * y - beta * z
    ]

# Time points and integration
dt = 0.01
num_steps = 10000
t = np.linspace(0, num_steps * dt, num_steps)

# Initialize arrays for storing the solution
xyz = np.zeros((num_steps, 3))
xyz[0] = (0., 1., 1.05)  # Initial condition

# Integrate the Lorenz equations using a simple Euler method
def integrate_lorenz():
    for i in range(num_steps-1):
        derivatives = lorenz_deriv(xyz[i], 0)
        xyz[i+1] = xyz[i] + dt * np.array(derivatives)
    return xyz

# Perform integration
integrate_lorenz()

# Function to create a static plot
def create_static_plot():
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title('Lorenz Attractor')

    # Plot the entire trajectory at once
    ax.plot(xyz[:, 0], xyz[:, 1], xyz[:, 2], lw=0.5, color='blue')
    ax.scatter(xyz[-1, 0], xyz[-1, 1], xyz[-1, 2], color='red', s=30)  # Highlight the end point

    # Set the axis limits
    ax.set_xlim((-30, 30))
    ax.set_ylim((-30, 30))
    ax.set_zlim((0, 60))

    # Add labels
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    # Set a good viewing angle
    ax.view_init(elev=30, azim=70)

    # Show the plot
    plt.tight_layout()
    return fig, ax

# Function to create an animation
def create_animation():
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title('Lorenz Attractor Animation')
    
    # Set the axis limits
    ax.set_xlim((-30, 30))
    ax.set_ylim((-30, 30))
    ax.set_zlim((0, 60))
    
    # Add labels
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    
    # Create a line object
    line, = ax.plot([], [], [], lw=0.5, color='blue')
    point = ax.scatter([], [], [], color='red', s=30)
    
    def init():
        line.set_data([], [])
        line.set_3d_properties([])
        point._offsets3d = ([], [], [])
        return line, point
    
    def update(frame):
        # Use a smaller step to make animation smoother
        i = frame * 20  # Show every 20th point
        if i >= num_steps:
            i = num_steps - 1
            
        x = xyz[:i, 0]
        y = xyz[:i, 1]
        z = xyz[:i, 2]
        
        line.set_data(x, y)
        line.set_3d_properties(z)
        
        point._offsets3d = ([xyz[i-1, 0]], [xyz[i-1, 1]], [xyz[i-1, 2]])
        
        return line, point
    
    ani = FuncAnimation(fig, update, frames=range(1, num_steps//20 + 1),
                        init_func=init, blit=True, interval=30)
    
    plt.tight_layout()
    return ani, fig

# Alternative interactive visualization using ipywidgets if available
def create_interactive_widget():
    try:
        import ipywidgets as widgets
        from IPython.display import display
        
        fig, ax = create_static_plot()
        
        # Create sliders for viewing angle
        elev_slider = widgets.FloatSlider(
            value=30, min=0, max=90, step=5, description='Elevation:'
        )
        azim_slider = widgets.FloatSlider(
            value=70, min=0, max=360, step=5, description='Azimuth:'
        )
        
        # Update function for the view
        def update_view(elev, azim):
            ax.view_init(elev=elev, azim=azim)
            fig.canvas.draw_idle()
        
        # Connect the sliders to the update function
        widgets.interact(update_view, elev=elev_slider, azim=azim_slider)
        
        return True
    except ImportError:
        print("ipywidgets not available for interactive controls")
        return False

# Main function to run the visualization
def main():
    # Try to create an interactive widget if in a Jupyter environment
    if 'ipykernel' in sys.modules:
        if create_interactive_widget():
            return
    
    # Otherwise, show the static plot and animation
    fig, ax = create_static_plot()
    plt.show()
    
    # Create and show animation
    ani, fig = create_animation()
    plt.show()
    
    # Uncomment to save animation
    # ani.save('lorenz_attractor.mp4', writer='ffmpeg', fps=30, dpi=150)

# Tests for the Lorenz system visualization
class TestLorenzVisualization(unittest.TestCase):
    def test_lorenz_integration(self):
        # Reset the xyz array
        global xyz
        xyz = np.zeros((num_steps, 3))
        xyz[0] = (0., 1., 1.05)
        
        result = integrate_lorenz()
        
        # Check that integration produced expected shape
        self.assertEqual(result.shape, (num_steps, 3))
        
        # Check that the values are not all zeros (integration happened)
        self.assertFalse(np.allclose(result, 0))
        
        # Check that the trajectory stays within expected bounds
        self.assertTrue(np.all(result[:, 0] > -30) and np.all(result[:, 0] < 30))
        self.assertTrue(np.all(result[:, 1] > -30) and np.all(result[:, 1] < 30))
        self.assertTrue(np.all(result[:, 2] > 0) and np.all(result[:, 2] < 60))
    
    def test_static_plot_creation(self):
        with patch('matplotlib.pyplot.figure') as mock_figure:
            mock_fig = MagicMock()
            mock_ax = MagicMock()
            mock_fig.add_subplot.return_value = mock_ax
            mock_figure.return_value = mock_fig
            
            fig, ax = create_static_plot()
            
            # Check that figure was created
            mock_figure.assert_called_once()
            # Check that 3D projection was used
            mock_fig.add_subplot.assert_called_once()
            self.assertIn('projection', mock_fig.add_subplot.call_args[1])
            self.assertEqual(mock_fig.add_subplot.call_args[1]['projection'], '3d')
            
            # Check that plot methods were called
            mock_ax.plot.assert_called_once()
            mock_ax.scatter.assert_called_once()
            mock_ax.set_xlim.assert_called_once()
            mock_ax.set_ylim.assert_called_once()
            mock_ax.set_zlim.assert_called_once()
    
    def test_animation_creation(self):
        with patch('matplotlib.pyplot.figure') as mock_figure, \
             patch('matplotlib.animation.FuncAnimation') as mock_func_animation:
            mock_fig = MagicMock()
            mock_ax = MagicMock()
            mock_fig.add_subplot.return_value = mock_ax
            mock_figure.return_value = mock_fig
            
            ani, fig = create_animation()
            
            # Check that FuncAnimation was called
            mock_func_animation.assert_called_once()
            
            # Check that the figure was created with correct settings
            mock_ax.set_xlim.assert_called_once_with((-30, 30))
            mock_ax.set_ylim.assert_called_once_with((-30, 30))
            mock_ax.set_zlim.assert_called_once_with((0, 60))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        unittest.main(argv=[sys.argv[0]])
    else:
        main()
