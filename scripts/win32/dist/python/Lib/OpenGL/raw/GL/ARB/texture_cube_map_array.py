'''OpenGL extension ARB.texture_cube_map_array

Automatically generated by the get_gl_extensions script, do not edit!
'''
from OpenGL import platform, constants, constant, arrays
from OpenGL import extensions
from OpenGL.GL import glget
import ctypes
EXTENSION_NAME = 'GL_ARB_texture_cube_map_array'
_DEPRECATED = False
GL_TEXTURE_CUBE_MAP_ARRAY = constant.Constant( 'GL_TEXTURE_CUBE_MAP_ARRAY', 0x9009 )
GL_TEXTURE_BINDING_CUBE_MAP_ARRAY = constant.Constant( 'GL_TEXTURE_BINDING_CUBE_MAP_ARRAY', 0x900A )
GL_PROXY_TEXTURE_CUBE_MAP_ARRAY = constant.Constant( 'GL_PROXY_TEXTURE_CUBE_MAP_ARRAY', 0x900B )
GL_SAMPLER_CUBE_MAP_ARRAY = constant.Constant( 'GL_SAMPLER_CUBE_MAP_ARRAY', 0x900C )
GL_SAMPLER_CUBE_MAP_ARRAY_SHADOW = constant.Constant( 'GL_SAMPLER_CUBE_MAP_ARRAY_SHADOW', 0x900D )
GL_INT_SAMPLER_CUBE_MAP_ARRAY = constant.Constant( 'GL_INT_SAMPLER_CUBE_MAP_ARRAY', 0x900E )
GL_UNSIGNED_INT_SAMPLER_CUBE_MAP_ARRAY = constant.Constant( 'GL_UNSIGNED_INT_SAMPLER_CUBE_MAP_ARRAY', 0x900F )


def glInitTextureCubeMapArrayARB():
    '''Return boolean indicating whether this extension is available'''
    return extensions.hasGLExtension( EXTENSION_NAME )
