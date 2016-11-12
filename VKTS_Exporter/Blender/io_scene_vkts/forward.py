# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8-80 compliant>

#
# Cycles deferred code.
#

VKTS_BINDING_UNIFORM_SAMPLER_BSDF_FORWARD_FIRST = 7

forwardGeneralDefineGLSL = """#define VKTS_MAX_LIGHTS 16

#define VKTS_PI 3.14159265

#define VKTS_FO_LINEAR_RANGE 0.08

#define VKTS_ONE_OVER_PI (1.0 / VKTS_PI)

#define VKTS_NORMAL_VALID_BIAS 0.1"""

forwardGeneralTextureGLSL = """layout (binding = 6) uniform sampler2D u_lut;
layout (binding = 5) uniform samplerCube u_specularCubemap;
layout (binding = 4) uniform samplerCube u_diffuseCubemap;"""

forwardGeneralFunctionsGLSL = """float pow_5(float x)
{
    float x2 = x * x;
    float x4 = x2 * x2;
    
    return x * x4;
}

//

float ndfTrowbridgeReitzGGX(float NdotH, float roughness)
{
    float alpha = roughness * roughness;
    
    float alpha2 = alpha * alpha;
    
    float divisor = NdotH * NdotH * (alpha2 - 1.0) + 1.0;
        
    return alpha2 / (VKTS_PI * divisor * divisor); 
}

//

float fresnel(float NdotV, float F0)
{
    return F0 + (1.0 - F0) * pow_5(1.0 - NdotV);
}

//

float geometricShadowingSchlick(float NdotV, float k)
{
    return NdotV / (NdotV * (1.0f - k) + k);
}

float geometricShadowingSmithSchlickGGX(float NdotL, float NdotV, float roughness)
{
    float k = roughness * roughness * 0.5f;

    return geometricShadowingSchlick(NdotL, k) * geometricShadowingSchlick(NdotV, k);
}

//

vec3 lambert(vec3 L, vec3 lightColor, vec3 N, vec3 baseColor)
{
    return lightColor * baseColor * max(dot(L, N), 0.0) * VKTS_ONE_OVER_PI;
}

vec3 iblLambert(vec3 N, vec3 baseColor)
{
    return baseColor * texture(u_diffuseCubemap, N).rgb;
}

vec3 cookTorrance(vec3 L, vec3 lightColor, vec3 N, vec3 V, float roughness, float F0)
{
    float NdotL = dot(N, L);
    float NdotV = dot(N, V);
    
    // Lighted and visible
    if (NdotL >= 0.0 && NdotV >= 0.0)
    {
        vec3 H = normalize(L + V);
        
        float NdotH = dot(N, H);
        float VdotH = dot(V, H);
        
        float D = ndfTrowbridgeReitzGGX(NdotH, roughness);
        float F = fresnel(VdotH, F0);
        float G = geometricShadowingSmithSchlickGGX(NdotL, NdotV, roughness);
        
        float f =  D * F * G / (4.0 * NdotL * NdotV);
        
        return f * lightColor;
    }
    
    return vec3(0.0, 0.0, 0.0);
}

vec3 iblCookTorrance(vec3 N, vec3 V, float roughness, vec3 baseColor, float F0)
{
    // Note: reflect takes incident vector.
    // Note: Use N instead of H for approximation.
    vec3 L = reflect(-V, N);
    
    float NdotL = dot(N, L);
    float NdotV = dot(N, V);
    
    // Lighted and visible
    if (NdotL > 0.0 && NdotV >= 0.0)
    {
        int levels = textureQueryLevels(u_specularCubemap); 
    
        float scaledRoughness = roughness * float(levels);
        
        float rLow = floor(scaledRoughness);
        float rHigh = ceil(scaledRoughness);    
        float rFraction = scaledRoughness - rLow;
        
        vec3 prefilteredColor = mix(textureLod(u_specularCubemap, L, rLow).rgb, textureLod(u_specularCubemap, L, rHigh).rgb, rFraction);

        vec2 envBRDF = texture(u_lut, vec2(NdotV, roughness)).rg;
        
        return baseColor * prefilteredColor * (F0 * envBRDF.x + envBRDF.y);
    }
    
    return vec3(0.0, 0.0, 0.0);
}"""

forwardOutDeclareGLSL = """layout (location = 0) out vec4 ob_fragColor;"""

forwardOutAssignGLSL = """// TODO: Add code based on resolve"""