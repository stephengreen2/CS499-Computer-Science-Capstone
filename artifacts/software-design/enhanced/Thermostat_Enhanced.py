#!/usr/bin/env python3
"""
Enhanced Thermostat System with Professional Software Engineering Practices

This module implements a smart thermostat control system using the Model-View-Controller
(MVC) design pattern, comprehensive unit testing, exception handling, and professional
documentation standards.

Author: Stephen Green
Version: 2.0
Date: July 20, 2025
"""

import time
import random
import unittest
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, List, Optional, Callable, Union
from unittest.mock import Mock, patch
import logging


# Configure logging for better debugging and monitoring
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Domain Value Objects and Enums
@dataclass(frozen=True)
class Temperature:
    """
    Value object representing temperature with validation and conversion capabilities.
    
    Attributes:
        value (float): Temperature value in Fahrenheit
        
    Raises:
        ValueError: If temperature is not numeric or outside reasonable range
    """
    value: float
    
    def __post_init__(self):
        """Validate temperature value during object creation."""
        if not isinstance(self.value, (int, float)):
            raise ValueError("Temperature must be numeric")
        if self.value < -100 or self.value > 200:
            raise ValueError("Temperature out of reasonable range (-100 to 200°F)")
    
    def __str__(self) -> str:
        """Return formatted temperature string."""
        return f"{self.value:.1f}°F"
    
    def is_above(self, other: 'Temperature') -> bool:
        """Check if this temperature is above another temperature."""
        return self.value > other.value
    
    def is_below(self, other: 'Temperature') -> bool:
        """Check if this temperature is below another temperature."""
        return self.value < other.value
    
    def rounded(self) -> int:
        """Return rounded temperature for display purposes."""
        return round(self.value)


@dataclass(frozen=True)
class SetPoint:
    """
    Value object representing target temperature with business rules and validation.
    
    Attributes:
        value (int): Target temperature in Fahrenheit
        
    Class Attributes:
        MIN_TEMP (int): Minimum allowable temperature (60°F)
        MAX_TEMP (int): Maximum allowable temperature (85°F)
        
    Raises:
        ValueError: If set point is not an integer or outside valid range
    """
    value: int
    
    MIN_TEMP = 60
    MAX_TEMP = 85
    
    def __post_init__(self):
        """Validate set point value during object creation."""
        if not isinstance(self.value, int):
            raise ValueError("SetPoint must be an integer")
        if self.value < self.MIN_TEMP or self.value > self.MAX_TEMP:
            raise ValueError(f"SetPoint must be between {self.MIN_TEMP} and {self.MAX_TEMP}°F")
    
    def increase(self) -> 'SetPoint':
        """
        Return new SetPoint increased by 1 degree, or current if at maximum.
        
        Returns:
            SetPoint: New SetPoint object with increased value or current if at max
        """
        if self.value < self.MAX_TEMP:
            return SetPoint(self.value + 1)
        return self
    
    def decrease(self) -> 'SetPoint':
        """
        Return new SetPoint decreased by 1 degree, or current if at minimum.
        
        Returns:
            SetPoint: New SetPoint object with decreased value or current if at min
        """
        if self.value > self.MIN_TEMP:
            return SetPoint(self.value - 1)
        return self
    
    def can_increase(self) -> bool:
        """Check if set point can be increased without exceeding maximum."""
        return self.value < self.MAX_TEMP
    
    def can_decrease(self) -> bool:
        """Check if set point can be decreased without going below minimum."""
        return self.value > self.MIN_TEMP
    
    def __str__(self) -> str:
        """Return formatted set point string."""
        return f"{self.value}°F"


class SystemMode(Enum):
    """
    Enumeration of valid system operating modes.
    
    Values:
        OFF: System is off, no heating or cooling
        HEAT: System is in heating mode
        COOL: System is in cooling mode
    """
    OFF = "OFF"
    HEAT = "HEAT"
    COOL = "COOL"
    
    @classmethod
    def from_string(cls, mode_str: str) -> 'SystemMode':
        """
        Create SystemMode from string input with validation.
        
        Args:
            mode_str (str): String representation of mode
            
        Returns:
            SystemMode: Corresponding system mode
            
        Raises:
            ValueError: If mode string is invalid
        """
        try:
            return cls(mode_str.upper())
        except ValueError:
            raise ValueError(f"Invalid mode: {mode_str}. Valid modes: OFF, HEAT, COOL")
    
    def next_mode(self) -> 'SystemMode':
        """
        Get the next mode in the cycle: OFF -> HEAT -> COOL -> OFF.
        
        Returns:
            SystemMode: Next mode in the cycle
        """
        cycle = [SystemMode.OFF, SystemMode.HEAT, SystemMode.COOL]
        current_index = cycle.index(self)
        return cycle[(current_index + 1) % len(cycle)]


class LEDColor(Enum):
    """LED color enumeration for display control."""
    RED = "Red"
    BLUE = "Blue"
    OFF = "Off"


class LEDState(Enum):
    """LED state enumeration for display control."""
    SOLID = "solid"
    PULSING = "pulsing"
    OFF = "off"


# Custom Exceptions with Detailed Error Information
class SensorError(Exception):
    """
    Exception raised when sensor operations fail.
    
    This exception is used to handle various sensor-related failures
    such as communication errors, reading failures, or sensor malfunctions.
    """
    pass


class ValidationError(Exception):
    """
    Exception raised when input validation fails.
    
    This exception is used for domain validation failures such as
    invalid temperature ranges or set point boundaries.
    """
    pass


class HardwareError(Exception):
    """
    Exception raised when hardware interface operations fail.
    
    This exception is used for GPIO, I2C, UART, or other hardware
    communication failures.
    """
    pass


# MODEL: Data Management and Business Logic
class ThermostatModel:
    """
    Model component implementing data management and business logic.
    
    This class handles temperature data, set point management, and system state
    according to the MVC pattern. It maintains the core business logic without
    any knowledge of user interface or hardware specifics.
    
    Attributes:
        _current_temp (Temperature): Current temperature reading
        _set_point (SetPoint): Target temperature setting
        _mode (SystemMode): Current operating mode
        _observers (List): List of observer callbacks for state changes
    """
    
    def __init__(self, initial_temp: float = 70.0, initial_set_point: int = 72):
        """
        Initialize the thermostat model with default values.
        
        Args:
            initial_temp (float): Initial temperature reading in Fahrenheit
            initial_set_point (int): Initial set point in Fahrenheit
            
        Raises:
            ValueError: If initial values are outside valid ranges
        """
        self._current_temp = Temperature(initial_temp)
        self._set_point = SetPoint(initial_set_point)
        self._mode = SystemMode.OFF
        self._observers: List[Callable] = []
        logger.info(f"ThermostatModel initialized: temp={initial_temp}°F, setpoint={initial_set_point}°F")
    
    def add_observer(self, observer: Callable) -> None:
        """
        Add an observer callback for state change notifications.
        
        Args:
            observer (Callable): Callback function to notify on state changes
        """
        self._observers.append(observer)
    
    def _notify_observers(self) -> None:
        """Notify all registered observers of state changes."""
        for observer in self._observers:
            try:
                observer()
            except Exception as e:
                logger.error(f"Observer notification failed: {e}")
    
    @property
    def current_temperature(self) -> Temperature:
        """Get the current temperature reading."""
        return self._current_temp
    
    @property
    def set_point(self) -> SetPoint:
        """Get the current set point."""
        return self._set_point
    
    @property
    def mode(self) -> SystemMode:
        """Get the current system mode."""
        return self._mode
    
    def update_temperature(self, new_temp: float) -> None:
        """
        Update the current temperature reading with validation.
        
        Args:
            new_temp (float): New temperature reading in Fahrenheit
            
        Raises:
            ValueError: If temperature is outside valid range
        """
        try:
            self._current_temp = Temperature(new_temp)
            self._notify_observers()
            logger.debug(f"Temperature updated to {self._current_temp}")
        except ValueError as e:
            logger.error(f"Invalid temperature update: {e}")
            raise ValidationError(f"Invalid temperature: {e}")
    
    def increase_set_point(self) -> bool:
        """
        Increase set point by one degree if within bounds.
        
        Returns:
            bool: True if set point was increased, False if at maximum
            
        Raises:
            ValidationError: If set point cannot be increased
        """
        if not self._set_point.can_increase():
            error_msg = f"Set point cannot exceed {SetPoint.MAX_TEMP} degrees"
            logger.warning(error_msg)
            raise ValidationError(error_msg)
        
        old_set_point = self._set_point
        self._set_point = self._set_point.increase()
        self._notify_observers()
        logger.info(f"Set point increased: {old_set_point.value}°F -> {self._set_point.value}°F")
        return True
    
    def decrease_set_point(self) -> bool:
        """
        Decrease set point by one degree if within bounds.
        
        Returns:
            bool: True if set point was decreased, False if at minimum
            
        Raises:
            ValidationError: If set point cannot be decreased
        """
        if not self._set_point.can_decrease():
            error_msg = f"Set point cannot go below {SetPoint.MIN_TEMP} degrees"
            logger.warning(error_msg)
            raise ValidationError(error_msg)
        
        old_set_point = self._set_point
        self._set_point = self._set_point.decrease()
        self._notify_observers()
        logger.info(f"Set point decreased: {old_set_point.value}°F -> {self._set_point.value}°F")
        return True
    
    def set_mode(self, mode: Union[str, SystemMode]) -> None:
        """
        Set the system operating mode with validation.
        
        Args:
            mode (Union[str, SystemMode]): New system mode
            
        Raises:
            ValidationError: If mode is invalid
        """
        try:
            if isinstance(mode, str):
                new_mode = SystemMode.from_string(mode)
            else:
                new_mode = mode
                
            old_mode = self._mode
            self._mode = new_mode
            self._notify_observers()
            logger.info(f"Mode changed: {old_mode.value} -> {new_mode.value}")
        except ValueError as e:
            logger.error(f"Invalid mode change: {e}")
            raise ValidationError(f"Invalid mode: {e}")
    
    def cycle_mode(self) -> None:
        """Cycle to the next mode in the sequence (OFF -> HEAT -> COOL -> OFF)."""
        old_mode = self._mode
        self._mode = self._mode.next_mode()
        self._notify_observers()
        logger.info(f"Mode cycled: {old_mode.value} -> {self._mode.value}")


# VIEW: Output Management (LEDs, LCD, UART)
class ThermostatView:
    """
    View component implementing output control for LEDs, display, and UART.
    
    This class handles all output operations including LED control, status display,
    and UART communications according to the MVC pattern. It abstracts the hardware
    interface details from the business logic.
    """
    
    def __init__(self, debug_mode: bool = False):
        """
        Initialize the view component.
        
        Args:
            debug_mode (bool): Enable debug output for development/testing
        """
        self.debug_mode = debug_mode
        self._led_state = LEDState.OFF
        self._led_color = LEDColor.OFF
        logger.info("ThermostatView initialized")
    
    def show_status(self, temp: Temperature, set_point: SetPoint, mode: SystemMode) -> None:
        """
        Display current system status in the standard format.
        
        Args:
            temp (Temperature): Current temperature reading
            set_point (SetPoint): Current set point
            mode (SystemMode): Current system mode
        """
        status_message = f"Current Temp: {temp.value:.1f} F | Set Point: {set_point.value} F | Mode: {mode.value}"
        print(status_message)
        
        if self.debug_mode:
            logger.debug(f"Status displayed: {status_message}")
    
    def control_led(self, state: LEDState, color: LEDColor) -> None:
        """
        Control LED display with consolidated logic to reduce duplication.
        
        This method abstracts LED control behaviors into reusable logic,
        eliminating redundant code from the original implementation.
        
        Args:
            state (LEDState): Desired LED state (solid, pulsing, off)
            color (LEDColor): Desired LED color (red, blue, off)
        """
        self._led_state = state
        self._led_color = color
        
        if state == LEDState.OFF:
            self._display_system_off()
        else:
            self._display_led_action(state, color)
        
        if self.debug_mode:
            logger.debug(f"LED control: {color.value} {state.value}")
    
    def _display_system_off(self) -> None:
        """Display system off message (consolidated LED off logic)."""
        print("System Off. All LEDs Off.")
    
    def _display_led_action(self, state: LEDState, color: LEDColor) -> None:
        """
        Display LED action message (consolidated LED control logic).
        
        Args:
            state (LEDState): LED state to display
            color (LEDColor): LED color to display
        """
        print(f"{color.value} LED {state.value}.")
    
    def show_error(self, error_message: str) -> None:
        """
        Display error messages with consistent formatting.
        
        Args:
            error_message (str): Error message to display
        """
        print(f"Error: {error_message}")
        logger.error(f"Error displayed: {error_message}")
    
    def send_uart_status(self, temp: Temperature, set_point: SetPoint, mode: SystemMode) -> str:
        """
        Format and send status over UART interface.
        
        Args:
            temp (Temperature): Current temperature
            set_point (SetPoint): Current set point  
            mode (SystemMode): Current mode
            
        Returns:
            str: Formatted UART message
        """
        uart_message = f"{mode.value},{temp.rounded()},{set_point.value}"
        
        # In a real implementation, this would send over actual UART
        if self.debug_mode:
            print(f"UART: {uart_message}")
            logger.debug(f"UART message sent: {uart_message}")
        
        return uart_message


# CONTROLLER: Input Processing and State Coordination
class ThermostatController:
    """
    Controller component implementing input processing and state coordination.
    
    This class processes button inputs, coordinates state changes between model
    and view, and implements the main system control logic according to the
    MVC pattern.
    
    Attributes:
        model (ThermostatModel): Reference to the data model
        view (ThermostatView): Reference to the view component
        sensor (TemperatureSensor): Temperature sensor interface
    """
    
    def __init__(self, model: ThermostatModel, view: ThermostatView, sensor: 'TemperatureSensor'):
        """
        Initialize the controller with model, view, and sensor dependencies.
        
        Args:
            model (ThermostatModel): Model component instance
            view (ThermostatView): View component instance
            sensor (TemperatureSensor): Temperature sensor interface
        """
        self.model = model
        self.view = view
        self.sensor = sensor
        
        # Register for model state change notifications
        self.model.add_observer(self._on_state_changed)
        
        logger.info("ThermostatController initialized")
    
    def handle_input(self, command: str) -> None:
        """
        Process user input commands with validation and error handling.
        
        Args:
            command (str): User input command
        """
        command = command.lower().strip()
        
        try:
            if command == 'heat':
                self.model.set_mode('HEAT')
            elif command == 'cool':
                self.model.set_mode('COOL')
            elif command == 'off':
                self.model.set_mode('OFF')
            elif command == 'up':
                self.model.increase_set_point()
            elif command == 'down':
                self.model.decrease_set_point()
            else:
                self.view.show_error("Unknown command. Valid commands: heat, cool, off, up, down, exit")
                
        except ValidationError as e:
            self.view.show_error(str(e))
        except Exception as e:
            logger.error(f"Unexpected error handling input '{command}': {e}")
            self.view.show_error("System error occurred")
    
    def run_cycle(self) -> None:
        """
        Execute one complete system cycle with exception handling.
        
        This method coordinates temperature reading, display updates, and
        HVAC control logic while handling potential sensor failures gracefully.
        """
        try:
            # Read temperature sensor with error handling
            new_temp = self.sensor.read_temperature()
            self.model.update_temperature(new_temp)
            
            # Update display
            self.view.show_status(
                self.model.current_temperature,
                self.model.set_point,
                self.model.mode
            )
            
            # Process HVAC control logic
            self._process_hvac_control()
            
        except SensorError as e:
            self.view.show_error(f"Temperature sensor failure: {e}")
            logger.error(f"Sensor error in run_cycle: {e}")
        except Exception as e:
            self.view.show_error("System error during cycle")
            logger.error(f"Unexpected error in run_cycle: {e}")
    
    def _process_hvac_control(self) -> None:
        """
        Process HVAC control logic with consolidated LED management.
        
        This method implements the core thermostat logic for determining
        when to heat, cool, or maintain temperature, with abstracted LED control.
        """
        current_temp = self.model.current_temperature
        set_point = self.model.set_point
        mode = self.model.mode
        
        if mode == SystemMode.HEAT:
            if current_temp.is_below(Temperature(set_point.value)):
                self.view.control_led(LEDState.PULSING, LEDColor.RED)
            else:
                self.view.control_led(LEDState.SOLID, LEDColor.RED)
                
        elif mode == SystemMode.COOL:
            if current_temp.is_above(Temperature(set_point.value)):
                self.view.control_led(LEDState.PULSING, LEDColor.BLUE)
            else:
                self.view.control_led(LEDState.SOLID, LEDColor.BLUE)
                
        elif mode == SystemMode.OFF:
            self.view.control_led(LEDState.OFF, LEDColor.OFF)
    
    def _on_state_changed(self) -> None:
        """Handle state change notifications from the model."""
        # Update HVAC control when state changes
        self._process_hvac_control()


# Hardware Interface Abstractions
class TemperatureSensor(ABC):
    """
    Abstract base class for temperature sensor interfaces.
    
    This abstraction allows for easy replacement of hardware interfaces
    without changing the system logic, supporting both real hardware
    and simulated sensors for testing.
    """
    
    @abstractmethod
    def read_temperature(self) -> float:
        """
        Read temperature from the sensor.
        
        Returns:
            float: Temperature reading in Fahrenheit
            
        Raises:
            SensorError: If sensor reading fails
        """
        pass


class SimulatedTemperatureSensor(TemperatureSensor):
    """
    Simulated temperature sensor for testing and development.
    
    This implementation provides realistic temperature simulation with
    configurable failure rates for comprehensive testing.
    """
    
    def __init__(self, failure_rate: float = 0.05, initial_temp: float = 70.0):
        """
        Initialize simulated sensor with failure simulation.
        
        Args:
            failure_rate (float): Probability of sensor failure (0.0 to 1.0)
            initial_temp (float): Starting temperature for simulation
        """
        self.failure_rate = failure_rate
        self._base_temp = initial_temp
        logger.info(f"SimulatedTemperatureSensor initialized: temp={initial_temp}°F, failure_rate={failure_rate}")
    
    def read_temperature(self) -> float:
        """
        Simulate temperature reading with realistic fluctuation and failures.
        
        Returns:
            float: Simulated temperature reading
            
        Raises:
            SensorError: If simulated sensor failure occurs
        """
        # Simulate sensor failure
        if random.random() < self.failure_rate:
            error_msg = "Temperature sensor failure (simulated)"
            logger.warning(error_msg)
            raise SensorError(error_msg)
        
        # Simulate realistic temperature fluctuation
        fluctuation = random.uniform(-0.5, 0.5)
        self._base_temp += fluctuation
        
        logger.debug(f"Sensor reading: {self._base_temp:.1f}°F")
        return self._base_temp


# COMPREHENSIVE UNIT TESTING WITH MOCKING
class TestThermostatModel(unittest.TestCase):
    """
    Unit tests for ThermostatModel component.
    
    These tests validate the model's data management and business logic
    functionality with comprehensive coverage of normal and edge cases.
    """
    
    def setUp(self):
        """Set up test fixtures for each test method."""
        self.model = ThermostatModel(initial_temp=70.0, initial_set_point=72)
    
    def test_initial_state(self):
        """Test that model initializes with correct default values."""
        self.assertEqual(self.model.current_temperature.value, 70.0)
        self.assertEqual(self.model.set_point.value, 72)
        self.assertEqual(self.model.mode, SystemMode.OFF)
    
    def test_temperature_update_valid(self):
        """Test temperature update with valid values."""
        self.model.update_temperature(75.5)
        self.assertEqual(self.model.current_temperature.value, 75.5)
    
    def test_temperature_update_invalid(self):
        """Test temperature update with invalid values raises exception."""
        with self.assertRaises(ValidationError):
            self.model.update_temperature(-150.0)  # Below valid range
    
    def test_set_point_increase_valid(self):
        """Test set point increase within valid bounds."""
        initial_value = self.model.set_point.value
        self.model.increase_set_point()
        self.assertEqual(self.model.set_point.value, initial_value + 1)
    
    def test_set_point_increase_at_maximum(self):
        """Test set point increase when already at maximum."""
        # Set to maximum first
        self.model._set_point = SetPoint(85)
        with self.assertRaises(ValidationError):
            self.model.increase_set_point()
    
    def test_set_point_decrease_valid(self):
        """Test set point decrease within valid bounds."""
        initial_value = self.model.set_point.value
        self.model.decrease_set_point()
        self.assertEqual(self.model.set_point.value, initial_value - 1)
    
    def test_set_point_decrease_at_minimum(self):
        """Test set point decrease when already at minimum."""
        # Set to minimum first
        self.model._set_point = SetPoint(60)
        with self.assertRaises(ValidationError):
            self.model.decrease_set_point()
    
    def test_mode_change_valid(self):
        """Test valid mode changes."""
        self.model.set_mode('HEAT')
        self.assertEqual(self.model.mode, SystemMode.HEAT)
        
        self.model.set_mode('COOL')
        self.assertEqual(self.model.mode, SystemMode.COOL)
        
        self.model.set_mode('OFF')
        self.assertEqual(self.model.mode, SystemMode.OFF)
    
    def test_mode_change_invalid(self):
        """Test invalid mode change raises exception."""
        with self.assertRaises(ValidationError):
            self.model.set_mode('INVALID')
    
    def test_mode_cycling(self):
        """Test mode cycling functionality."""
        # Start at OFF
        self.assertEqual(self.model.mode, SystemMode.OFF)
        
        # Cycle to HEAT
        self.model.cycle_mode()
        self.assertEqual(self.model.mode, SystemMode.HEAT)
        
        # Cycle to COOL
        self.model.cycle_mode()
        self.assertEqual(self.model.mode, SystemMode.COOL)
        
        # Cycle back to OFF
        self.model.cycle_mode()
        self.assertEqual(self.model.mode, SystemMode.OFF)


class TestThermostatView(unittest.TestCase):
    """
    Unit tests for ThermostatView component.
    
    These tests validate the view's output functionality using mocking
    to simulate hardware interfaces and verify correct behavior.
    """
    
    def setUp(self):
        """Set up test fixtures for each test method."""
        self.view = ThermostatView(debug_mode=False)
    
    @patch('builtins.print')
    def test_show_status_format(self, mock_print):
        """Test status display format matches expected output."""
        temp = Temperature(72.5)
        set_point = SetPoint(75)
        mode = SystemMode.HEAT
        
        self.view.show_status(temp, set_point, mode)
        
        expected_output = "Current Temp: 72.5 F | Set Point: 75 F | Mode: HEAT"
        mock_print.assert_called_with(expected_output)
    
    @patch('builtins.print')
    def test_led_control_heating_active(self, mock_print):
        """Test LED control for active heating mode."""
        self.view.control_led(LEDState.PULSING, LEDColor.RED)
        mock_print.assert_called_with("Red LED pulsing.")
    
    @patch('builtins.print')
    def test_led_control_system_off(self, mock_print):
        """Test LED control for system off state."""
        self.view.control_led(LEDState.OFF, LEDColor.OFF)
        mock_print.assert_called_with("System Off. All LEDs Off.")
    
    @patch('builtins.print')
    def test_error_display(self, mock_print):
        """Test error message display formatting."""
        self.view.show_error("Test error message")
        mock_print.assert_called_with("Error: Test error message")
    
    def test_uart_message_format(self):
        """Test UART message formatting."""
        temp = Temperature(72.0)
        set_point = SetPoint(75)
        mode = SystemMode.HEAT
        
        uart_msg = self.view.send_uart_status(temp, set_point, mode)
        
        self.assertEqual(uart_msg, "HEAT,72,75")


class TestThermostatController(unittest.TestCase):
    """
    Unit tests for ThermostatController component.
    
    These tests validate the controller's input processing and coordination
    logic using mocked dependencies for isolated testing.
    """
    
    def setUp(self):
        """Set up test fixtures with mocked dependencies."""
        self.model = ThermostatModel()
        self.view = ThermostatView()
        self.sensor = Mock(spec=TemperatureSensor)
        self.controller = ThermostatController(self.model, self.view, self.sensor)
    
    def test_handle_mode_commands(self):
        """Test handling of mode change commands."""
        self.controller.handle_input('heat')
        self.assertEqual(self.model.mode, SystemMode.HEAT)
        
        self.controller.handle_input('cool')
        self.assertEqual(self.model.mode, SystemMode.COOL)
        
        self.controller.handle_input('off')
        self.assertEqual(self.model.mode, SystemMode.OFF)
    
    def test_handle_setpoint_commands(self):
        """Test handling of set point adjustment commands."""
        initial_setpoint = self.model.set_point.value
        
        self.controller.handle_input('up')
        self.assertEqual(self.model.set_point.value, initial_setpoint + 1)
        
        self.controller.handle_input('down')
        self.assertEqual(self.model.set_point.value, initial_setpoint)
    
    @patch('builtins.print')
    def test_handle_invalid_command(self, mock_print):
        """Test handling of invalid commands."""
        self.controller.handle_input('invalid')
        # Should display error message
        mock_print.assert_called()
    
    def test_run_cycle_normal_operation(self):
        """Test normal system cycle operation."""
        # Mock sensor to return valid temperature
        self.sensor.read_temperature.return_value = 72.5
        
        # Should not raise any exceptions
        self.controller.run_cycle()
        
        # Verify sensor was called
        self.sensor.read_temperature.assert_called_once()
        
        # Verify temperature was updated in model
        self.assertEqual(self.model.current_temperature.value, 72.5)
    
    @patch('builtins.print')
    def test_run_cycle_sensor_failure(self, mock_print):
        """Test system cycle with sensor failure."""
        # Mock sensor to raise SensorError
        self.sensor.read_temperature.side_effect = SensorError("Sensor failed")
        
        # Should handle exception gracefully
        self.controller.run_cycle()
        
        # Should display error message
        mock_print.assert_called()


class TestHVACControlLogic(unittest.TestCase):
    """
    Integration tests for HVAC control logic.
    
    These tests validate the complete thermostat control logic
    including LED behaviors for different operating conditions.
    """
    
    def setUp(self):
        """Set up test fixtures for integration testing."""
        self.model = ThermostatModel()
        self.view = ThermostatView()
        self.sensor = Mock(spec=TemperatureSensor)
        self.controller = ThermostatController(self.model, self.view, self.sensor)
    
    @patch('builtins.print')
    def test_heating_mode_temperature_below_setpoint(self, mock_print):
        """Test heating mode when temperature is below set point."""
        # Set up conditions: temp below set point, heating mode
        self.sensor.read_temperature.return_value = 68.0
        self.model.set_mode('HEAT')
        self.model.update_temperature(68.0)
        
        # Run system cycle
        self.controller.run_cycle()
        
        # Should show pulsing red LED
        calls = mock_print.call_args_list
        led_call = next((call for call in calls if "Red LED pulsing" in str(call)), None)
        self.assertIsNotNone(led_call, "Should display pulsing red LED")
    
    @patch('builtins.print')
    def test_heating_mode_temperature_at_setpoint(self, mock_print):
        """Test heating mode when temperature reaches set point."""
        # Set up conditions: temp at set point, heating mode
        self.sensor.read_temperature.return_value = 72.0
        self.model.set_mode('HEAT')
        self.model.update_temperature(72.0)
        
        # Run system cycle
        self.controller.run_cycle()
        
        # Should show solid red LED
        calls = mock_print.call_args_list
        led_call = next((call for call in calls if "Red LED solid" in str(call)), None)
        self.assertIsNotNone(led_call, "Should display solid red LED")
    
    @patch('builtins.print')
    def test_cooling_mode_temperature_above_setpoint(self, mock_print):
        """Test cooling mode when temperature is above set point."""
        # Set up conditions: temp above set point, cooling mode
        self.sensor.read_temperature.return_value = 76.0
        self.model.set_mode('COOL')
        self.model.update_temperature(76.0)
        
        # Run system cycle
        self.controller.run_cycle()
        
        # Should show pulsing blue LED
        calls = mock_print.call_args_list
        led_call = next((call for call in calls if "Blue LED pulsing" in str(call)), None)
        self.assertIsNotNone(led_call, "Should display pulsing blue LED")
    
    @patch('builtins.print')
    def test_off_mode_all_leds_off(self, mock_print):
        """Test off mode shows all LEDs off."""
        # Set up conditions: any temperature, off mode
        self.sensor.read_temperature.return_value = 72.0
        self.model.set_mode('OFF')
        
        # Run system cycle
        self.controller.run_cycle()
        
        # Should show system off message
        calls = mock_print.call_args_list
        led_call = next((call for call in calls if "System Off. All LEDs Off" in str(call)), None)
        self.assertIsNotNone(led_call, "Should display system off message")


class TestSensorIntegration(unittest.TestCase):
    """
    Integration tests for sensor interface and error handling.
    
    These tests validate sensor failure handling and recovery
    mechanisms using mocked hardware interfaces.
    """
    
    def setUp(self):
        """Set up test fixtures for sensor testing."""
        self.sensor = SimulatedTemperatureSensor(failure_rate=0.0)  # No failures for controlled testing
    
    def test_sensor_normal_reading(self):
        """Test normal sensor reading operation."""
        temp = self.sensor.read_temperature()
        self.assertIsInstance(temp, float)
        self.assertGreaterEqual(temp, -100)
        self.assertLessEqual(temp, 200)
    
    def test_sensor_failure_simulation(self):
        """Test sensor failure simulation and error handling."""
        failing_sensor = SimulatedTemperatureSensor(failure_rate=1.0)  # Always fail
        
        with self.assertRaises(SensorError):
            failing_sensor.read_temperature()


class TestSystemIntegration(unittest.TestCase):
    """
    Full system integration tests.
    
    These tests validate the complete system functionality with
    all components working together, simulating real-world usage scenarios.
    """
    
    def setUp(self):
        """Set up complete system for integration testing."""
        self.model = ThermostatModel()
        self.view = ThermostatView()
        self.sensor = SimulatedTemperatureSensor(failure_rate=0.0)
        self.controller = ThermostatController(self.model, self.view, self.sensor)
    
    def test_complete_heating_cycle(self):
        """Test complete heating cycle from cold start."""
        # Start with cold temperature
        self.sensor._base_temp = 65.0
        
        # Set to heating mode
        self.controller.handle_input('heat')
        self.assertEqual(self.model.mode, SystemMode.HEAT)
        
        # Run a cycle
        self.controller.run_cycle()
        
        # Temperature should be updated and system should be in heating mode
        self.assertIsInstance(self.model.current_temperature, Temperature)
        self.assertEqual(self.model.mode, SystemMode.HEAT)
    
    def test_setpoint_boundary_enforcement(self):
        """Test set point boundary enforcement in full system."""
        # Test upper boundary
        self.model._set_point = SetPoint(84)  # One below max
        self.controller.handle_input('up')  # Should work
        self.assertEqual(self.model.set_point.value, 85)
        
        # Try to exceed maximum
        with patch('builtins.print') as mock_print:
            self.controller.handle_input('up')  # Should show error
            mock_print.assert_called()
    
    @patch('builtins.print')
    def test_error_recovery(self, mock_print):
        """Test system error recovery and graceful degradation."""
        # Create a sensor that will fail
        failing_sensor = SimulatedTemperatureSensor(failure_rate=1.0)
        self.controller.sensor = failing_sensor
        
        # System should handle failure gracefully
        self.controller.run_cycle()
        
        # Should display error message
        mock_print.assert_called()


# MAIN APPLICATION CLASS
class ThermostatApplication:
    """
    Main application class implementing the complete thermostat system.
    
    This class coordinates all MVC components and provides the main
    application entry point with comprehensive error handling and
    professional software engineering practices.
    """
    
    def __init__(self, debug_mode: bool = False, initial_temp: float = 70.0):
        """
        Initialize the complete thermostat application.
        
        Args:
            debug_mode (bool): Enable debug output and logging
            initial_temp (float): Initial temperature for simulation
        """
        self.debug_mode = debug_mode
        
        # Initialize MVC components
        self.model = ThermostatModel(initial_temp=initial_temp)
        self.view = ThermostatView(debug_mode=debug_mode)
        self.sensor = SimulatedTemperatureSensor(initial_temp=initial_temp)
        self.controller = ThermostatController(self.model, self.view, self.sensor)
        
        logger.info(f"ThermostatApplication initialized (debug={debug_mode})")
    
    def run(self) -> None:
        """
        Run the main application loop with comprehensive error handling.
        
        This method implements the main user interaction loop with
        graceful error handling and clean shutdown procedures.
        """
        print("=" * 60)
        print("Enhanced Smart Thermostat System v2.0")
        print("Implementing Professional Software Engineering Practices")
        print("=" * 60)
        print("Commands: heat, cool, off, up, down, exit")
        print("Features: MVC Architecture, Exception Handling, Unit Testing")
        print("=" * 60)
        
        try:
            while True:
                try:
                    user_input = input("\nEnter command: ").strip()
                    
                    if user_input.lower() == 'exit':
                        print("\nShutting down thermostat system...")
                        logger.info("Application shutdown requested by user")
                        break
                    
                    # Process user input
                    self.controller.handle_input(user_input)
                    
                    # Run system cycle
                    self.controller.run_cycle()
                    
                except EOFError:
                    print("\nInput stream closed. Exiting...")
                    break
                except KeyboardInterrupt:
                    print("\nKeyboard interrupt received. Exiting...")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error in main loop: {e}")
                    self.view.show_error("System error occurred. Please try again.")
                    
        except Exception as e:
            logger.critical(f"Critical error in application: {e}")
            print("Critical system error. Application will exit.")
        finally:
            self._cleanup()
    
    def _cleanup(self) -> None:
        """Perform cleanup operations before application exit."""
        print("Performing system cleanup...")
        logger.info("Application cleanup completed")
        print("Thermostat system shutdown complete.")


# UTILITY FUNCTIONS FOR TESTING AND DEVELOPMENT
def run_comprehensive_tests() -> None:
    """
    Run comprehensive unit and integration tests.
    
    This function executes all test suites and provides detailed
    reporting for development and quality assurance purposes.
    """
    print("=" * 60)
    print("Running Comprehensive Test Suite")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestThermostatModel,
        TestThermostatView,
        TestThermostatController,
        TestHVACControlLogic,
        TestSensorIntegration,
        TestSystemIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Suite Summary")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\n')[0]}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('\n')[-2]}")
    
    return result.wasSuccessful()


def demonstrate_features() -> None:
    """
    Demonstrate key features and capabilities of the enhanced system.
    
    This function showcases the improvements made to the original
    thermostat code, highlighting professional software engineering practices.
    """
    print("=" * 60)
    print("Enhanced Thermostat Features Demonstration")
    print("=" * 60)
    
    # Create system components
    model = ThermostatModel()
    view = ThermostatView(debug_mode=True)
    sensor = SimulatedTemperatureSensor()
    controller = ThermostatController(model, view, sensor)
    
    print("\n1. MVC Architecture Demonstration:")
    print("   - Model: Handles data and business logic")
    print("   - View: Manages all output (LEDs, display, UART)")
    print("   - Controller: Processes input and coordinates components")
    
    print("\n2. Exception Handling Demonstration:")
    try:
        model.increase_set_point()
        print("   ✓ Set point increased successfully")
    except ValidationError as e:
        print(f"   ✓ Validation error handled: {e}")
    
    print("\n3. Input Validation Demonstration:")
    try:
        model.set_mode("INVALID")
    except ValidationError as e:
        print(f"   ✓ Invalid input rejected: {e}")
    
    print("\n4. Sensor Failure Handling:")
    failing_sensor = SimulatedTemperatureSensor(failure_rate=1.0)
    controller.sensor = failing_sensor
    print("   ✓ Sensor failure simulation ready")
    
    print("\n5. Consolidated LED Control:")
    view.control_led(LEDState.PULSING, LEDColor.RED)
    print("   ✓ LED control abstracted and consolidated")
    
    print("\n6. Professional Documentation:")
    print("   ✓ Comprehensive docstrings for all classes and methods")
    print("   ✓ Type hints for better code clarity")
    print("   ✓ Detailed inline comments")
    
    print("\n" + "=" * 60)
    print("All enhancements successfully demonstrated!")
    print("=" * 60)


# MAIN EXECUTION BLOCK
if __name__ == "__main__":
    """
    Main execution block with command-line argument support.
    
    This block provides multiple execution modes for development,
    testing, and production use cases.
    """
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            # Run comprehensive test suite
            success = run_comprehensive_tests()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == 'demo':
            # Run feature demonstration
            demonstrate_features()
            sys.exit(0)
        elif sys.argv[1] == 'debug':
            # Run application in debug mode
            app = ThermostatApplication(debug_mode=True)
            app.run()
        else:
            print("Usage: python thermostat.py [test|demo|debug]")
            sys.exit(1)
    else:
        # Run normal application
        app = ThermostatApplication(debug_mode=False)
        app.run()