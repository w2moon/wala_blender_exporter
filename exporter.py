import bpy;
import struct;
from bpy.props import (BoolProperty,
                       FloatProperty,
                       StringProperty,
                       EnumProperty,
                       )
from bpy_extras.io_utils import ExportHelper
from math import sqrt
def uv_key(uv):
    return round(uv[0],6),round(uv[1],6)

class FileHeader:
    version = 0;
    numVertices = 0;
    numNormals = 0;
    numIndices  = 0;
    numTangent = 0;
    numBinormal = 0;
    
    def __init__(self, version, numVertices, numIndices, numNormals,numTangent,numBinormal):
        self.version = version;
        self.numVertices = numVertices;
        self.numNormals = numNormals;
        self.numIndices  = numIndices;
        self.numTangent = numTangent;
        self.numBinormal = numBinormal;
    
    def write(self, file):
        file.write(struct.pack('hhhhhh', self.version, self.numVertices, self.numIndices, self.numNormals,self.numTangent,self.numBinormal));
        
class FileBody:
    mesh      = None;
    img       = None;
    uvs       = [];
    tri_list  = [];
    
    def __init__(self, mesh):
        self.mesh = mesh;
        
    def write(self, file):
        if self.mesh.img is not None:
            file.write(struct.pack('I%ds' % len(self.mesh.img), len(self.mesh.img),self.mesh.img));
        else:
            file.write(struct.pack('I', 0));
        
        for tri in self.mesh.point_list:
            file.write(struct.pack('fff', tri.x, tri.y, tri.z));

        i=0
        for tri in self.mesh.point_list:
            file.write(struct.pack('h', i));
            i=i+1

        for tri in self.mesh.point_list:
            file.write(struct.pack('ff',tri.u,tri.v));

        if self.mesh.normal_num() > 0 :
            for tri in self.mesh.point_list:
                file.write(struct.pack('fff', tri.nx, tri.ny, tri.nz));

        if self.mesh.tangent_num() > 0 :
            for tri in self.mesh.point_list:
                file.write(struct.pack('fff', tri.tx, tri.ty, tri.tz));

        if self.mesh.binormal_num() > 0 :
            for tri in self.mesh.point_list:
                file.write(struct.pack('fff', tri.bx, tri.by, tri.bz));

                

class PointInfo(object):

    def __init__(self,x = 0.0,y = 0.0,z = 0.0,u = 0.0,v = 0.0,nx = 0.0,ny = 0.0,nz = 0.0,tx = 0.0,ty = 0.0,tz = 0.0,bx = 0.0,by = 0.0,bz = 0.0):
        self.x = x
        self.y = y
        self.z = z
        self.u = u
        self.v = v
        self.nx = nx
        self.ny = ny
        self.nz = nz
        self.tx = tx
        self.ty = ty
        self.tz = tz
        self.bx = bx
        self.by = by
        self.bz = bz
    

class MeshData(object):

    __slots__ = "img","point_list"

    def __init__(self,mesh):
        self.extract(mesh)

    def normal_num(self):
        if Exporter.use_normals:
            print("normal")
            return len(self.point_list)
        return 0

    def tangent_num(self):
        print(dir(Exporter.use_tangents))
        if Exporter.use_tangents:
            print("tangent")
            return len(self.point_list)
        return 0

    def binormal_num(self):
        if Exporter.use_tangents:
            print("binormal")
            return len(self.point_list)
        return 0
        
    def vertice_num(self):
        return len(self.point_list)

    def indice_num(self):
        return len(self.point_list)

    def normalize(self,v):
        l = sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2])
        v[0] = v[0]/l
        v[1] = v[1]/l
        v[2] = v[2]/l
        return v

    def calc_tangent(self,mesh,uv,face,face_type):
        if face_type == 1:
            edge1 = mesh.vertices[face[1]].co - mesh.vertices[face[0]].co
            edge2 = mesh.vertices[face[2]].co - mesh.vertices[face[0]].co
            edge1uv = (uv[1][0] - uv[0][0],uv[1][1] - uv[0][1])
            edge2uv = (uv[2][0] - uv[0][0],uv[2][1] - uv[0][1])

            cp = edge1uv[0] * edge2uv[1] - edge1uv[1] * edge2uv[0];

            mul = 1
            if cp != 0.0:
                mul = 1.0/cp
            tangent = (edge1*edge2uv[1] - edge2*edge1uv[1])*mul
            binormal = (edge1*-edge2uv[0] + edge2*edge1uv[0])*mul
        else:
            edge1 = mesh.vertices[face[2]].co - mesh.vertices[face[0]].co
            edge2 = mesh.vertices[face[3]].co - mesh.vertices[face[0]].co
            edge1uv = (uv[2][0] - uv[0][0],uv[2][1] - uv[0][1])
            edge2uv = (uv[3][0] - uv[0][0],uv[3][1] - uv[0][1])

            cp = edge1uv[0] * edge2uv[1] - edge1uv[1] * edge2uv[0];

            mul = 1
            if cp != 0.0:
                mul = 1.0/cp
            tangent = (edge1*edge2uv[1] - edge2*edge1uv[1])*mul
            binormal = (edge1*-edge2uv[0] + edge2*edge1uv[0])*mul
        return tangent,binormal
            

    def extract(self, mesh):
        self.point_list = [];

        self.img = None;
        do_uv = bool(mesh.tessface_uv_textures)
        
        for i,face in enumerate(mesh.tessfaces):
            # Store access to the vertices
            face_verts = face.vertices;
            uf = mesh.tessface_uv_textures.active.data[i] if do_uv else None

            if do_uv:
                f_uv = uf.uv;
                img = uf.image if uf else None
                if img is not None:
                    self.img = img.name
                
            # If there are 3 vertices the face is a triangle else the face is a quads
            if len(face_verts) == 3:
                # Create a new triangle wrapper for
                if do_uv:
                    tangent,binormal = self.calc_tangent(mesh,f_uv,face_verts,1)
                    #t2 = face.loops[0].calc_tangent()
                    #print("tangent %f %f %f,%f %f %f",tangent[0],tangent[1],tangent[2],t2[0],t2[1],t2[2])
                    new_tri = PointInfo(mesh.vertices[face_verts[0]].co[0], mesh.vertices[face_verts[0]].co[1], mesh.vertices[face_verts[0]].co[2],round(f_uv[0][0],6),round(f_uv[0][1],6),mesh.vertices[face_verts[0]].normal[0],mesh.vertices[face_verts[0]].normal[1],mesh.vertices[face_verts[0]].normal[2],tangent[0],tangent[1],tangent[2],binormal[0],binormal[1],binormal[2]);
                    self.point_list.append(new_tri);
                    new_tri = PointInfo(mesh.vertices[face_verts[1]].co[0], mesh.vertices[face_verts[1]].co[1], mesh.vertices[face_verts[1]].co[2],round(f_uv[1][0],6),round(f_uv[1][1],6),mesh.vertices[face_verts[1]].normal[0],mesh.vertices[face_verts[1]].normal[1],mesh.vertices[face_verts[1]].normal[2],tangent[0],tangent[1],tangent[2],binormal[0],binormal[1],binormal[2]);
                    self.point_list.append(new_tri);
                    new_tri = PointInfo(mesh.vertices[face_verts[2]].co[0], mesh.vertices[face_verts[2]].co[1], mesh.vertices[face_verts[2]].co[2],round(f_uv[2][0],6),round(f_uv[2][1],6),mesh.vertices[face_verts[2]].normal[0],mesh.vertices[face_verts[2]].normal[1],mesh.vertices[face_verts[2]].normal[2],tangent[0],tangent[1],tangent[2],binormal[0],binormal[1],binormal[2]);
                    self.point_list.append(new_tri);
                    
                else:
                    new_tri = PointInfo(mesh.vertices[face_verts[0]].co[0], mesh.vertices[face_verts[0]].co[1], mesh.vertices[face_verts[0]].co[2])
                    self.point_list.append(new_tri);
                    new_tri = PointInfo(mesh.vertices[face_verts[1]].co[0], mesh.vertices[face_verts[1]].co[1], mesh.vertices[face_verts[1]].co[2])
                    self.point_list.append(new_tri);
                    new_tri = PointInfo(mesh.vertices[face_verts[2]].co[0], mesh.vertices[face_verts[2]].co[1], mesh.vertices[face_verts[2]].co[2])
                    self.point_list.append(new_tri);
            else:

                if do_uv:
                    tangent,binormal = self.calc_tangent(mesh,f_uv,face_verts,1)
                    tangent2,binormal2 = self.calc_tangent(mesh,f_uv,face_verts,0)
                    tangent3 = self.normalize([tangent[0],tangent[1],tangent[2]])
                    binormal3 = self.normalize([binormal[0],binormal[1],binormal[2]])

                    tangent = self.normalize(tangent + tangent2)
                    binormal = self.normalize(binormal + binormal2)
                    #t2 = face.loops[0].calc_tangent()
                    #print("tangent %f %f %f,%f %f %f",tangent[0],tangent[1],tangent[2],t2[0],t2[1],t2[2])
                    new_tri = PointInfo(mesh.vertices[face_verts[0]].co[0], mesh.vertices[face_verts[0]].co[1], mesh.vertices[face_verts[0]].co[2],round(f_uv[0][0],6),round(f_uv[0][1],6),mesh.vertices[face_verts[0]].normal[0],mesh.vertices[face_verts[0]].normal[1],mesh.vertices[face_verts[0]].normal[2],tangent[0],tangent[1],tangent[2],binormal[0],binormal[1],binormal[2]);
                    self.point_list.append(new_tri);
                    new_tri = PointInfo(mesh.vertices[face_verts[1]].co[0], mesh.vertices[face_verts[1]].co[1], mesh.vertices[face_verts[1]].co[2],round(f_uv[1][0],6),round(f_uv[1][1],6),mesh.vertices[face_verts[1]].normal[0],mesh.vertices[face_verts[1]].normal[1],mesh.vertices[face_verts[1]].normal[2],tangent3[0],tangent3[1],tangent3[2],binormal3[0],binormal3[1],binormal3[2]);
                    self.point_list.append(new_tri);
                    new_tri = PointInfo(mesh.vertices[face_verts[2]].co[0], mesh.vertices[face_verts[2]].co[1], mesh.vertices[face_verts[2]].co[2],round(f_uv[2][0],6),round(f_uv[2][1],6),mesh.vertices[face_verts[2]].normal[0],mesh.vertices[face_verts[2]].normal[1],mesh.vertices[face_verts[2]].normal[2],tangent[0],tangent[1],tangent[2],binormal[0],binormal[1],binormal[2]);
                    self.point_list.append(new_tri);
                    #tangent,binormal = self.calc_tangent(mesh,f_uv,face_verts,0)
                    #t2 = face.loops[0].calc_tangent()
                    #print("tangent %f %f %f,%f %f %f",tangent[0],tangent[1],tangent[2],t2[0],t2[1],t2[2])
                    tangent3 = self.normalize([tangent2[0],tangent2[1],tangent2[2]])
                    binormal3 = self.normalize([binormal2[0],binormal2[1],binormal2[2]])
                    new_tri = PointInfo(mesh.vertices[face_verts[0]].co[0], mesh.vertices[face_verts[0]].co[1], mesh.vertices[face_verts[0]].co[2],round(f_uv[0][0],6),round(f_uv[0][1],6),mesh.vertices[face_verts[0]].normal[0],mesh.vertices[face_verts[0]].normal[1],mesh.vertices[face_verts[0]].normal[2],tangent[0],tangent[1],tangent[2],binormal[0],binormal[1],binormal[2]);
                    self.point_list.append(new_tri);
                    new_tri = PointInfo(mesh.vertices[face_verts[2]].co[0], mesh.vertices[face_verts[2]].co[1], mesh.vertices[face_verts[2]].co[2],round(f_uv[2][0],6),round(f_uv[2][1],6),mesh.vertices[face_verts[2]].normal[0],mesh.vertices[face_verts[2]].normal[1],mesh.vertices[face_verts[2]].normal[2],tangent3[0],tangent3[1],tangent3[2],binormal3[0],binormal3[1],binormal3[2]);
                    self.point_list.append(new_tri);
                    new_tri = PointInfo(mesh.vertices[face_verts[3]].co[0], mesh.vertices[face_verts[3]].co[1], mesh.vertices[face_verts[3]].co[2],round(f_uv[3][0],6),round(f_uv[3][1],6),mesh.vertices[face_verts[3]].normal[0],mesh.vertices[face_verts[3]].normal[1],mesh.vertices[face_verts[3]].normal[2],tangent[0],tangent[1],tangent[2],binormal[0],binormal[1],binormal[2]);
                    self.point_list.append(new_tri);
                else:
                    new_tri = PointInfo(mesh.vertices[face_verts[0]].co[0], mesh.vertices[face_verts[0]].co[1], mesh.vertices[face_verts[0]].co[2])
                    self.point_list.append(new_tri);
                    new_tri = PointInfo(mesh.vertices[face_verts[1]].co[0], mesh.vertices[face_verts[1]].co[1], mesh.vertices[face_verts[1]].co[2])
                    self.point_list.append(new_tri);
                    new_tri = PointInfo(mesh.vertices[face_verts[2]].co[0], mesh.vertices[face_verts[2]].co[1], mesh.vertices[face_verts[2]].co[2])
                    self.point_list.append(new_tri);
                    new_tri = PointInfo(mesh.vertices[face_verts[0]].co[0], mesh.vertices[face_verts[0]].co[1], mesh.vertices[face_verts[0]].co[2])
                    self.point_list.append(new_tri);
                    new_tri = PointInfo(mesh.vertices[face_verts[2]].co[0], mesh.vertices[face_verts[2]].co[1], mesh.vertices[face_verts[2]].co[2])
                    self.point_list.append(new_tri);
                    new_tri = PointInfo(mesh.vertices[face_verts[3]].co[0], mesh.vertices[face_verts[3]].co[1], mesh.vertices[face_verts[3]].co[2])
                    self.point_list.append(new_tri);

class UVWrapper(object):
    __slots__ = "uv","offset";

    def __init__(self,uv = (0,0)):
        self.uv = round(uv[0],6),round(uv[1],6);
        
class TriangleWrapper(object):
    __slots__ = "vertex_indices", "offset";
    
    def __init__(self, vertex_index=(0,0,0)):
        self.vertex_indices = vertex_index;

class Exporter(bpy.types.Operator, ExportHelper):
    bl_idname       = "export_whill_format.wmh";
    bl_label        = "Whill Data Exporter";
    bl_options      = {'PRESET'};
    
    filename_ext    = ".wmh";

    # context group
    use_skeleton = BoolProperty(name="Skeleton",description="Export Skeleton",default=False,)

    use_animation = BoolProperty(name="Animation",description="Write out an wmh for each frame",default=False,)
    use_normals = BoolProperty(name="Include Normals",description="Write out the normals",default=True,)
    use_tangents = BoolProperty(name="Include Tangents",description="Write out the tangents",default=False,)
    
    # This method will be used to extract triangle vertex and index data from 3D Objects in the Blender scene.
    # This method can export objects built from either triangle or quad primitives.
    def extract_triangles(self, mesh):
        # Create an empty array to store out triangles.
        triangle_list = [];

        # Loop through all of the faces defined in the mesh
        for i,face in enumerate(mesh.tessfaces):
            # Store access to the vertices
            face_verts = face.vertices;
            # If there are 3 vertices the face is a triangle else the face is a quad
            if len(face_verts) == 3:
                # Create a new triangle wrapper for
                new_tri = TriangleWrapper((face_verts[0], face_verts[1], face_verts[2]));
               
                triangle_list.append(new_tri);
            else:
                new_tri_1 = TriangleWrapper((face_verts[0], face_verts[1], face_verts[2]));
                new_tri_2 = TriangleWrapper((face_verts[0], face_verts[2], face_verts[3]));

                triangle_list.append(new_tri_1);
                triangle_list.append(new_tri_2);
            
        return triangle_list;

    def extract_img(self, mesh):
        img = None;
        do_uv = bool(mesh.tessface_uv_textures)
        for i, face in enumerate(mesh.tessfaces):
            uf = mesh.tessface_uv_textures.active.data[i] if do_uv else None
            if do_uv:
                img = uf.image if uf else None
                if img is not None:
                    img = img.name
                    return img
                
        return img

    def extract_uvs(self, mesh, num):
        uvs = [None]*num;
        do_uv = bool(mesh.tessface_uv_textures)
        
        for i,face in enumerate(mesh.tessfaces):
            # Store access to the vertices
            face_verts = face.vertices;
            uf = mesh.tessface_uv_textures.active.data[i] if do_uv else None

            if do_uv:
                f_uv = uf.uv;
                
            # If there are 3 vertices the face is a triangle else the face is a quads
            if len(face_verts) == 3:
                # Create a new triangle wrapper for
                if do_uv:
                    uvs[face_verts[0]] = UVWrapper(f_uv[0])
                    uvs[face_verts[1]] = UVWrapper(f_uv[1])
                    uvs[face_verts[2]] = UVWrapper(f_uv[2])
                else:
                    uvs[face_verts[0]] = UVWrapper()
                    uvs[face_verts[1]] = UVWrapper()
                    uvs[face_verts[2]] = UVWrapper()
            else:

                if do_uv:
                    uvs[face_verts[0]] = UVWrapper(f_uv[0])
                    uvs[face_verts[1]] = UVWrapper(f_uv[1])
                    uvs[face_verts[2]] = UVWrapper(f_uv[2])
                    uvs[face_verts[0]] = UVWrapper(f_uv[0])
                    uvs[face_verts[2]] = UVWrapper(f_uv[2])
                    uvs[face_verts[3]] = UVWrapper(f_uv[3])
                else:
                    uvs[face_verts[0]] = UVWrapper()
                    uvs[face_verts[1]] = UVWrapper()
                    uvs[face_verts[2]] = UVWrapper()
                    uvs[face_verts[0]] = UVWrapper()
                    uvs[face_verts[2]] = UVWrapper()
                    uvs[face_verts[3]] = UVWrapper()
                    
        return uvs
            
    def execute(self, context):
        # Ensure Blender is currently in OBJECT mode to allow data access. 
        bpy.ops.object.mode_set(mode='OBJECT');
    
        # Set the default return state to FINISHED
        result = {'FINISHED'};
    
        # Check that the currently selected object contains mesh data for exporting
        ob = context.object;
        if not ob or ob.type != 'MESH' or not ob.select:
            raise NameError("Cannot export: object %s is not a mesh" % ob);
    
        # Create a file body object for storing the data to be written to file.
        obdata = MeshData(ob.to_mesh(context.scene,True,'PREVIEW'))

        
        fileBody = FileBody(obdata);
        #fileBody.tri_list = self.extract_triangles(fileBody.mesh);
        #fileBody.img = self.extract_img(fileBody.mesh)
        #fileBody.uvs = self.extract_uvs(fileBody.mesh,len(fileBody.mesh.vertices))
    
        # Create a file header object with data stored in the body section
        fileHeader = FileHeader(
            0,
            obdata.vertice_num(),
            obdata.indice_num(),
            obdata.normal_num(),
            obdata.tangent_num(),
            obdata.binormal_num());
        
        # Open the file for writing
        file = open(self.filepath, 'bw');
        # Write the file data
        fileHeader.write(file);
        fileBody.write(file);
        # Close the file
        file.close();
    
        return result;
