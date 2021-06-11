"""threedvector provides common methods for working with 3D vectors in both Spherical and Cartesian coordinates."""
from operator import add, sub
from numbers import Number
import math


def copy(other):
    """Returns a copy of vector other

    Returns:
    (Vector)
    """
    return Vector(other.magnitude(), other.theta(), other.phi())


class Vector:
    """ Create a 3D Vector.

    Keyword arguments:
    radius_x -- length in Spherical coordinates, x in Cartesian coordinates (default 0.0)
    theta_y -- polar angle in Spherical coordinates, y in Cartesian coordinates (default 0.0)
    phi_z=0 -- azimuthal angle in Spherical coordinates, z in Cartesian coordinates (default 0.0)
    coords -- identifies coordinate system of arguments as either "spherical" or "cartesian" (default "spherical")
    """

    def __init__(self, radius_x=0.0, theta_y=0.0, phi_z=0.0, coords="spherical"):
        if coords == "cartesian":
            self.__init_cartesian(radius_x, theta_y, phi_z)
        elif coords == "spherical":
            self.__init_spherical(radius_x, theta_y, phi_z)
        else:
            raise AttributeError(
                "Incorrect parameter for coords keyword in Vector __init__")

    def __init_spherical(self, radius, theta, phi):
        self.__set_magnitude(radius)
        self.__set_theta(theta)
        self.__set_phi(phi)

    def __init_cartesian(self, x, y, z):
        temp_vector = self.__to_spherical([x, y, z])
        self.__radius = temp_vector.magnitude()
        self.__theta = temp_vector.theta()
        self.__phi = temp_vector.phi()

    def __to_spherical(self, c_vector):
        x, y, z = self.__get_xyz(c_vector)
        radius = self.__get_radius(c_vector)
        theta = math.atan2(y, x)
        phi = math.atan2(math.sqrt(x**2 + y**2), z)
        return Vector(radius, math.degrees(theta), math.degrees(phi))

    def __get_xyz(self, vector):
        return vector[0], vector[1], vector[2]

    def __get_radius(self, vector):
        return math.sqrt(vector[0]**2 + vector[1]**2 + vector[2]**2)

    def __sin(self, angle):
        return math.sin(math.radians(angle))

    def __cos(self, angle):
        return math.cos(math.radians(angle))

    def __set_magnitude(self, magnitude):
        self.__radius = magnitude

    def __set_theta(self, theta):
        self.__theta = theta % 360

    def __set_phi(self, phi):
        self.__phi = phi % 360

    def __str__(self):
        return (f"({self.magnitude()}, {self.theta()}, {self.phi()})")

    def __add__(self, other):
        summed_vectors = list(
            map(add, self.cartesian(), other.cartesian()))
        return self.__to_spherical(summed_vectors)

    def __sub__(self, other):
        subbed_vectors = list(
            map(sub, self.cartesian(), other.cartesian()))
        return self.__to_spherical(subbed_vectors)

    def __rmul__(self, factor):
        return self.__mul__(factor)

    def __mul__(self, factor):
        if not isinstance(factor, Number):
            raise TypeError(
                "Built in mulitplication only valid with scalar values.  For dot product or cross product, use respective dot() and cross() functions.")
        product = self.__radius * factor
        return Vector(product, self.theta(), self.phi())

    def __div__(self, divisor):
        try:
            division = self.magnitude() / divisor
        except TypeError as ex:
            print(ex)
            print("\nCan only divide vectors by scalar.")
        else:
            return Vector(division, self.theta(), self.phi())

    def __eq__(self, other):
        return self.magnitude() == other.magnitude()

    def __gt__(self, other):
        return self.magnitude() > other.magnitude()

    def __ge__(self, other):
        return self.__eq__(other) or self.__gt__(other)

    def is_same(self, other):
        return self.magnitude() == other.magnitude() and self.theta() == other.theta() and self.phi() == other.phi()

    def cartesian(self):
        """Returns the Cartesian cooridnates of the current instance of Vector

        Retruns:
        (list) [x, y, z]
        """
        radius = self.magnitude()
        cos_phi = self.__cos(self.phi())
        sin_phi = self.__sin(self.phi())
        cos_theta = self.__cos(self.theta())
        sin_theta = self.__sin(self.theta())
        x = radius*sin_phi*cos_theta
        y = radius*sin_phi*sin_theta
        z = radius*cos_phi
        return [x, y, z]

    def dot(self, other):
        """Calculates the dot product between instance of Vector and Vector other

        Parameters:
        other (Vector): vector to compute dot product with

        Retruns:
        (float) scalar value of dot product
        """
        c_self = self.cartesian()
        c_other = other.cartesian()
        return c_self[0]*c_other[0] + c_self[1]*c_other[1] + c_self[2]*c_other[2]

    def cross(self, other):
        """Calculates the cross product between instance of Vector and Vector other

        Parameters:
        other (Vector): vector to compute cross product with

        Returns:
        (Vector) cross product of two vectors
        """
        c_self = self.cartesian()
        c_other = other.cartesian()
        cross_x = c_self[1]*c_other[2] - c_self[2]*c_other[1]
        cross_y = c_self[2]*c_other[0] - c_self[0]*c_other[2]
        cross_z = c_self[0]*c_other[1] - c_self[1]*c_other[0]
        return self.__to_spherical([cross_x, cross_y, cross_z])

    def angle(self, other):
        """Calculates the in-plane angle between instance of Vector and Vector other

        Parameters:
        other (Vector): vector to compute cross product with

        Returns:
        (float) in-plane angle between two vectors in degrees
        """
        if (self.magnitude() * other.magnitude() == 0) or self.is_same(other):
            return 0
        return math.degrees(math.acos(self.dot(other)/(self.magnitude() * other.magnitude())))

    def unit(self):
        """Calculates the unit vector of the current Vector instance

        Returns:
        (Vector) unit vector of self
        """
        c_self = self.cartesian()
        radius = self.__get_radius(c_self)
        if radius == 0:
            raise ZeroDivisionError(
                "Cannot calculate the unit vector of a zero length vector.")
        return self.__to_spherical([x/radius for x in c_self])

    def magnitude(self):
        """Returns the length of a vector

        Returns:
        (float) length of a vector
        """
        return self.__radius

    def theta(self):
        """Returns the polar angle, theta of a vector

        Returns:
        (float) polar angle of a vector
        """
        return self.__theta

    def phi(self):
        """Returns the azimuthal angle, phi of a vector

        Returns:
        (float) azimuthal angle of a vector
        """
        return self.__phi

    def set_magnitude(self, magnitude):
        """Sets the length of a vector

        """
        self.__set_magnitude(magnitude)

    def set_theta(self, theta):
        """Sets the polar angle, theta of a vector

        """
        self.__set_theta(theta)

    def set_phi(self, phi):
        """Sets the azimuthal angle, phi of a vector

        """
        self.__set_phi(phi)
